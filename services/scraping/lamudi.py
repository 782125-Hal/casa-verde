"""Scraper Lamudi — Tijuana con Playwright."""
from services.scraping.base import BaseScraper, ScraperError
from services.scraping.normalizer import limpiar_texto


class LamudiScraper(BaseScraper):
    fuente_nombre = 'Lamudi'
    base_url = 'https://www.lamudi.com.mx'
    wait_selector = 'a[href*="/"], [class*="listing"], [class*="Listing"]'

    TIPO_PATH = {
        'casa': 'casa',
        'terreno': 'terreno',
        'departamento': 'departamento',
        'local': 'local',
    }

    def _url_busqueda(self, config):
        slug = self.zona_slug(config.zona.nombre)
        tipo = self.TIPO_PATH.get(config.tipo_inmueble or 'casa', 'casa')
        return f'{self.base_url}/{slug}/{tipo}/for-sale/'

    def buscar(self, config):
        url = self._url_busqueda(config)
        try:
            html = self.fetch(url)
        except ScraperError:
            return []

        soup = self.parse_html(html)
        resultados = []
        patrones = ['/detalle/', '/property/', '/inmueble/', f'/{self.zona_slug(config.zona.nombre)}/']

        for link, full_url in self.extraer_links(soup, patrones):
            if '/for-sale/' in full_url and full_url.count('/') < 6:
                continue
            if 'for-sale' in full_url and not any(x in full_url for x in ('/detalle/', '/property/', '/inmueble/')):
                if full_url.endswith('/for-sale/') or full_url.endswith('/for-sale'):
                    continue

            card = link.find_parent(['article', 'div', 'li']) or link
            titulo = limpiar_texto(link.get('title') or link.get_text())
            if len(titulo) < 8:
                continue

            precio_el = card.select_one('[class*="price"], [class*="Price"], [data-price]')
            item = {
                'titulo': titulo[:200],
                'precio_texto': precio_el.get_text() if precio_el else '',
                'url_anuncio': full_url.split('?')[0],
                'tipo_inmueble': config.tipo_inmueble or 'casa',
            }
            ubicacion = card.select_one('[class*="location"], [class*="Location"], [class*="address"]')
            if ubicacion:
                item['direccion'] = limpiar_texto(ubicacion.get_text())

            resultados.append(item)
            if len(resultados) >= self.max_resultados:
                break

        return resultados

    def parse_detalle_url(self, url):
        html = self.fetch(url)
        soup = self.parse_html(html)

        for data in self.extraer_json_ld(soup):
            if data.get('@type') in ('Product', 'RealEstateListing', 'Apartment', 'House', 'SingleFamilyResidence'):
                offers = data.get('offers', {})
                if isinstance(offers, list):
                    offers = offers[0] if offers else {}
                return {
                    'titulo': limpiar_texto(data.get('name')),
                    'descripcion': limpiar_texto(data.get('description')),
                    'precio_texto': str(offers.get('price') or data.get('price', '')),
                    'url_anuncio': url,
                    'superficie_texto': str(data.get('floorSize', '')),
                }

        titulo = soup.find('h1')
        precio = soup.select_one('[class*="price"], [class*="Price"], h2')
        desc = soup.select_one('[class*="description"], [class*="Description"]')
        return {
            'titulo': limpiar_texto(titulo.get_text()) if titulo else '',
            'descripcion': limpiar_texto(desc.get_text()) if desc else '',
            'precio_texto': limpiar_texto(precio.get_text()) if precio else '',
            'url_anuncio': url,
        }