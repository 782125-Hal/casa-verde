"""Scraper Mercado Libre Inmuebles — Tijuana con filtro geográfico."""
from services.scraping.base import BaseScraper, ScraperError
from services.scraping.geo_filter import filtrar_listados
from services.scraping.normalizer import limpiar_texto


class MercadoLibreScraper(BaseScraper):
    fuente_nombre = 'Mercado Libre'
    base_url = 'https://listado.mercadolibre.com.mx'
    wait_selector = '.poly-card__content, li.ui-search-layout__item, .ui-search-layout'
    max_escaneo = 60

    TIPO_MAP = {
        'casa': 'casas',
        'departamento': 'departamentos',
        'terreno': 'terrenos',
        'local': 'locales-comerciales',
    }

    def _url_busqueda(self, config):
        slug = self.zona_slug(config.zona.nombre)
        tipo = self.TIPO_MAP.get(config.tipo_inmueble or 'casa', 'casas')
        return (
            f'{self.base_url}/inmuebles/{tipo}/baja-california/tijuana/'
            f'{slug}_Desde_49_NoIndex_True'
        )

    def _extraer_ubicacion_card(self, card):
        loc = card.select_one(
            '.poly-component__location, .ui-search-item__location, '
            '[class*="location"], [class*="address"]',
        )
        return limpiar_texto(loc.get_text()) if loc else ''

    def buscar(self, config):
        url = self._url_busqueda(config)
        try:
            html = self.fetch(url)
        except ScraperError:
            return []

        soup = self.parse_html(html)
        crudos = []
        vistos = set()

        cards = soup.select('.poly-card__content, li.ui-search-layout__item')
        for card in cards[:self.max_escaneo]:
            link = card.select_one(
                'a.poly-component__title, a.ui-search-link, a[href*="MLM-"]',
            )
            if not link:
                continue

            href = link.get('href', '').split('#')[0].split('?')[0]
            if not href or href in vistos or 'click' in href:
                continue
            vistos.add(href)

            titulo = limpiar_texto(link.get_text())
            if len(titulo) < 10:
                continue

            fraccion = card.select_one(
                '.poly-price__current .andes-money-amount__fraction, '
                '.andes-money-amount__fraction',
            )
            centavos = card.select_one('.andes-money-amount__cents')
            precio_texto = fraccion.get_text(strip=True) if fraccion else ''
            if centavos and precio_texto:
                precio_texto = f'{precio_texto}.{centavos.get_text(strip=True)}'

            ubicacion = self._extraer_ubicacion_card(card)

            crudos.append({
                'titulo': titulo[:200],
                'precio_texto': precio_texto,
                'url_anuncio': href,
                'tipo_inmueble': config.tipo_inmueble or 'casa',
                'direccion': ubicacion or '',
                'descripcion': ubicacion,
            })

        filtrados, rechazados = filtrar_listados(crudos, config.zona)
        return filtrados[:self.max_resultados]

    def parse_detalle_url(self, url):
        html = self.fetch(url)
        soup = self.parse_html(html)

        for data in self.extraer_json_ld(soup):
            offers = data.get('offers', {})
            if isinstance(offers, list):
                offers = offers[0] if offers else {}
            if data.get('name'):
                return {
                    'titulo': limpiar_texto(data.get('name')),
                    'descripcion': limpiar_texto(data.get('description')),
                    'precio_texto': str(offers.get('price', '')),
                    'url_anuncio': url,
                }

        h1 = soup.find('h1')
        precio = soup.select_one('.andes-money-amount__fraction')
        desc = soup.select_one('[class*="description"], .ui-pdp-description')
        ubicacion = soup.select_one('[class*="location"], .ui-pdp-media__subtitle')
        return {
            'titulo': limpiar_texto(h1.get_text()) if h1 else '',
            'descripcion': limpiar_texto(desc.get_text()) if desc else '',
            'precio_texto': limpiar_texto(precio.get_text()) if precio else '',
            'direccion': limpiar_texto(ubicacion.get_text()) if ubicacion else '',
            'url_anuncio': url,
        }