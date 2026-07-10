"""Scraper Vivanuncios — búsqueda inmobiliaria Tijuana."""
from urllib.parse import quote, urljoin

from services.scraping.base import BaseScraper
from services.scraping.normalizer import limpiar_texto


class VivanunciosScraper(BaseScraper):
    fuente_nombre = 'Vivanuncios'
    base_url = 'https://www.vivanuncios.com.mx'
    wait_selector = 'a[href*="/a-venta-inmuebles/"], [class*="listing"]'

    def _url_busqueda(self, config):
        zona = config.zona.nombre
        tipo = config.tipo_inmueble or 'casa'
        q = quote(f'{tipo} {zona} tijuana venta')
        return f'{self.base_url}/s-venta-inmuebles/q-{q}'

    def buscar(self, config):
        url = self._url_busqueda(config)
        try:
            html = self.fetch(url)
        except Exception:
            return []

        soup = self.parse_html(html)
        resultados = []
        vistos = set()

        for link in soup.select('a[href*="/a-venta-inmuebles/"], a[href*="/anuncio/"]'):
            href = link.get('href', '')
            if not href or href in vistos:
                continue
            full_url = urljoin(self.base_url, href)
            vistos.add(href)

            card = link.find_parent(['article', 'div', 'li']) or link
            precio_el = card.select_one('[class*="price"], [class*="precio"]')

            item = {
                'titulo': limpiar_texto(link.get_text())[:200] or 'Listado Vivanuncios',
                'precio_texto': limpiar_texto(precio_el.get_text()) if precio_el else '',
                'url_anuncio': full_url,
                'tipo_inmueble': config.tipo_inmueble or 'casa',
            }
            if len(item['titulo']) > 5:
                resultados.append(item)
            if len(resultados) >= self.max_resultados:
                break

        return resultados

    def parse_detalle_url(self, url):
        html = self.fetch(url)
        soup = self.parse_html(html)
        h1 = soup.find('h1')
        precio = soup.select_one('[class*="price"], [data-testid*="price"]')
        desc = soup.select_one('[class*="description"], #description')
        return {
            'titulo': limpiar_texto(h1.get_text()) if h1 else '',
            'descripcion': limpiar_texto(desc.get_text()) if desc else '',
            'precio_texto': limpiar_texto(precio.get_text()) if precio else '',
            'url_anuncio': url,
        }