"""Scraper Inmuebles24 — Tijuana con Playwright."""
from urllib.parse import urljoin

from services.scraping.base import BaseScraper, ScraperError
from services.scraping.normalizer import limpiar_texto


class Inmuebles24Scraper(BaseScraper):
    fuente_nombre = 'Inmuebles24'
    base_url = 'https://www.inmuebles24.com'
    wait_selector = 'a[href*=".html"], [class*="posting"], [class*="card"]'

    TIPO_MAP = {
        'casa': 'casas',
        'departamento': 'departamentos',
        'terreno': 'terrenos',
        'local': 'locales-comerciales',
    }

    def _url_busqueda(self, config):
        slug = self.zona_slug(config.zona.nombre)
        tipo = self.TIPO_MAP.get(config.tipo_inmueble or 'casa', 'casas')
        return f'{self.base_url}/{tipo}-venta-{slug}-tijuana.html'

    def buscar(self, config):
        url = self._url_busqueda(config)
        try:
            html = self.fetch(url)
        except ScraperError:
            return []

        soup = self.parse_html(html)
        resultados = []

        for link, full_url in self.extraer_links(soup, ['.html', '/propiedades/']):
            if 'venta-' in full_url and full_url.count('-') < 4:
                continue
            if full_url.endswith('.html') and 'tijuana' not in full_url.lower():
                if 'venta' not in full_url:
                    continue

            card = link.find_parent(['div', 'article', 'li']) or link
            titulo = limpiar_texto(link.get('title') or link.get_text())
            if len(titulo) < 10:
                continue

            precio_el = card.select_one('[class*="price"], [class*="precio"], .price')
            resultados.append({
                'titulo': titulo[:200],
                'precio_texto': limpiar_texto(precio_el.get_text()) if precio_el else '',
                'url_anuncio': full_url.split('?')[0],
                'tipo_inmueble': config.tipo_inmueble or 'casa',
            })
            if len(resultados) >= self.max_resultados:
                break

        return resultados

    def parse_detalle_url(self, url):
        html = self.fetch(url)
        soup = self.parse_html(html)
        for data in self.extraer_json_ld(soup):
            offers = data.get('offers', {})
            if isinstance(offers, list):
                offers = offers[0] if offers else {}
            if offers.get('price') or data.get('name'):
                return {
                    'titulo': limpiar_texto(data.get('name')),
                    'descripcion': limpiar_texto(data.get('description')),
                    'precio_texto': str(offers.get('price', '')),
                    'url_anuncio': url,
                }
        h1 = soup.find('h1')
        precio = soup.select_one('[class*="price"], .price-value, [data-qa="price"]')
        return {
            'titulo': limpiar_texto(h1.get_text()) if h1 else '',
            'precio_texto': limpiar_texto(precio.get_text()) if precio else '',
            'url_anuncio': url,
        }