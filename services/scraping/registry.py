"""Registro de scrapers por fuente de datos."""
from services.scraping.inmuebles24 import Inmuebles24Scraper
from services.scraping.lamudi import LamudiScraper
from services.scraping.mercadolibre import MercadoLibreScraper
from services.scraping.propiedades_com import PropiedadesComScraper
from services.scraping.vivanuncios import VivanunciosScraper

SCRAPER_MAP = {
    'mercado libre': MercadoLibreScraper,
    'mercadolibre': MercadoLibreScraper,
    'lamudi': LamudiScraper,
    'propiedades': PropiedadesComScraper,
    'propiedades.com': PropiedadesComScraper,
    'vivanuncios': VivanunciosScraper,
    'inmuebles24': Inmuebles24Scraper,
}

DOMINIO_MAP = {
    'mercadolibre.com.mx': MercadoLibreScraper,
    'casa.mercadolibre.com.mx': MercadoLibreScraper,
    'lamudi.com.mx': LamudiScraper,
    'propiedades.com': PropiedadesComScraper,
    'vivanuncios.com.mx': VivanunciosScraper,
    'inmuebles24.com': Inmuebles24Scraper,
}


def _instanciar(clase, fuente, playwright_session=None):
    return clase(fuente, playwright_session=playwright_session)


def obtener_scraper(fuente, playwright_session=None):
    nombre = fuente.nombre.lower()
    for clave, clase in SCRAPER_MAP.items():
        if clave in nombre:
            return _instanciar(clase, fuente, playwright_session)
    return None


def obtener_scraper_por_url(url, playwright_session=None):
    from urllib.parse import urlparse

    dominio = urlparse(url).netloc.lower().replace('www.', '')
    for clave, clase in DOMINIO_MAP.items():
        if clave in dominio:
            from mercado.models import FuenteDatos
            fuente = FuenteDatos.objects.filter(nombre__icontains=clave.split('.')[0]).first()
            if not fuente:
                fuente = FuenteDatos(nombre=clase.fuente_nombre, tipo='portal')
            return _instanciar(clase, fuente, playwright_session)
    return None