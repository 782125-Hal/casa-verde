"""Scraper Propiedades.com — Tijuana."""
from urllib.parse import quote, urljoin

from services.scraping.base import BaseScraper
from services.scraping.normalizer import limpiar_texto


class PropiedadesComScraper(BaseScraper):
    fuente_nombre = 'Propiedades.com'
    base_url = 'https://propiedades.com'
    wait_selector = 'a[href*="/inmuebles/"], [class*="property"], [class*="listing"]'

    def _url_busqueda(self, config):
        zona = self.zona_slug(config.zona.nombre).replace('-', ' ')
        tipo = config.tipo_inmueble or 'casa'
        query = quote(f'{tipo} {zona} tijuana')
        return f'{self.base_url}/buscar?ubicacion=tijuana-baja-california&q={query}'

    def buscar(self, config):
        url = self._url_busqueda(config)
        try:
            html = self.fetch(url)
        except Exception:
            return []

        soup = self.parse_html(html)
        resultados = []
        vistos = set()

        for link in soup.select('a[href*="/inmuebles/"], a[href*="/propiedades/"]'):
            href = link.get('href', '')
            if not href or href in vistos:
                continue
            full_url = urljoin(self.base_url, href)
            if full_url in vistos:
                continue
            vistos.add(href)
            vistos.add(full_url)

            card = link.find_parent(['article', 'div', 'li']) or link
            precio_el = card.select_one('[class*="price"], [class*="precio"], [data-price]')
            precio_texto = ''
            if precio_el:
                precio_texto = precio_el.get('data-price') or precio_el.get_text()

            item = {
                'titulo': limpiar_texto(link.get('title') or link.get_text()) or 'Listado Propiedades.com',
                'precio_texto': limpiar_texto(precio_texto),
                'url_anuncio': full_url,
                'tipo_inmueble': config.tipo_inmueble or 'casa',
            }
            resultados.append(item)
            if len(resultados) >= self.max_resultados:
                break

        return resultados

    def parse_detalle_url(self, url):
        html = self.fetch(url)
        soup = self.parse_html(html)

        for data in self.extraer_json_ld(soup):
            if data.get('@type') in ('Product', 'RealEstateListing', 'House', 'Apartment'):
                offers = data.get('offers', {})
                if isinstance(offers, list):
                    offers = offers[0] if offers else {}
                return {
                    'titulo': limpiar_texto(data.get('name')),
                    'descripcion': limpiar_texto(data.get('description')),
                    'precio_texto': str(offers.get('price', '')),
                    'url_anuncio': url,
                }

        h1 = soup.find('h1')
        precio = soup.select_one('h2, [class*="price"], [class*="precio"]')
        return {
            'titulo': limpiar_texto(h1.get_text()) if h1 else '',
            'precio_texto': limpiar_texto(precio.get_text()) if precio else '',
            'url_anuncio': url,
        }