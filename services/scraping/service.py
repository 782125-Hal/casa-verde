"""Orquestador de scraping — Casa Verde Fase 4 + Playwright."""
import logging
import traceback

from django.conf import settings
from django.utils import timezone

from mercado.models import FuenteDatos, ScrapeEjecucion
from services.registro import registrar_desde_fuente
from services.scraping.normalizer import normalizar_listing
from services.scraping.registry import obtener_scraper, obtener_scraper_por_url

logger = logging.getLogger(__name__)


class ScrapingService:
    @classmethod
    def _usar_playwright(cls):
        if not getattr(settings, 'SCRAPING_USE_PLAYWRIGHT', True):
            return False
        from services.scraping.playwright_fetcher import playwright_disponible
        return playwright_disponible()

    @classmethod
    def _recolectar_listings(cls, config, fuentes, playwright_session=None):
        """Fase 1: solo HTTP/Playwright, sin tocar la BD."""
        recolectado = []

        for fuente in fuentes:
            scraper = obtener_scraper(fuente, playwright_session=playwright_session)
            if not scraper:
                recolectado.append({'fuente': fuente, 'listings': None, 'error': 'sin scraper'})
                continue
            try:
                listings = scraper.buscar(config)
                recolectado.append({'fuente': fuente, 'listings': listings, 'error': None})
            except Exception as exc:
                recolectado.append({'fuente': fuente, 'listings': [], 'error': str(exc)})

        return recolectado

    @classmethod
    def ejecutar_para_config(cls, config):
        motor = 'playwright' if cls._usar_playwright() else 'requests'
        resumen = {
            'encontrados': 0, 'nuevos': 0, 'actualizados': 0,
            'errores': 0, 'fuentes': [], 'motor': motor,
        }

        fuentes = list(FuenteDatos.objects.filter(activa=True, tipo='portal'))

        if cls._usar_playwright():
            from services.scraping.playwright_fetcher import PlaywrightSession
            with PlaywrightSession() as pw_session:
                recolectado = cls._recolectar_listings(config, fuentes, playwright_session=pw_session)
        else:
            recolectado = cls._recolectar_listings(config, fuentes, playwright_session=None)

        for item in recolectado:
            resultado = cls._persistir_fuente(config, item, motor)
            cls._acumular_resumen(resumen, resultado)

        return resumen

    @classmethod
    def _acumular_resumen(cls, resumen, resultado):
        resumen['encontrados'] += resultado['encontrados']
        resumen['nuevos'] += resultado['nuevos']
        resumen['actualizados'] += resultado['actualizados']
        resumen['errores'] += resultado['errores']
        resumen['fuentes'].append(resultado)

    @classmethod
    def _persistir_fuente(cls, config, item, motor):
        fuente = item['fuente']
        ejecucion = ScrapeEjecucion.objects.create(
            configuracion=config, fuente=fuente, zona=config.zona, estado='en_proceso',
        )
        encontrados = nuevos = actualizados = errores = 0
        log_lines = [f'Motor: {motor}']

        if item.get('error') == 'sin scraper':
            ejecucion.estado = 'omitido'
            ejecucion.log = 'Sin scraper registrado'
            ejecucion.finalizado_en = timezone.now()
            ejecucion.save()
            return {'fuente': fuente.nombre, 'encontrados': 0, 'nuevos': 0, 'actualizados': 0, 'errores': 0, 'omitido': True}

        listings = item.get('listings') or []
        if item.get('error'):
            log_lines.append(f'Error scrape: {item["error"]}')

        try:
            encontrados = len(listings)
            log_lines.append(f'Listados encontrados (post-filtro geo): {encontrados}')
            if fuente.nombre.lower().find('mercado libre') >= 0:
                log_lines.append(f'Zona filtro: {config.zona.nombre}')

            for raw in listings:
                try:
                    normalizado = normalizar_listing(raw, config.zona_id)
                    if not normalizado:
                        errores += 1
                        continue
                    descripcion = normalizado.pop('descripcion_sistema', 'Detectada automáticamente')
                    normalizado['descripcion'] = normalizado.get('descripcion') or descripcion
                    _, es_nueva = registrar_desde_fuente(
                        normalizado, fuente, capturado_por=config.usuario,
                    )
                    if es_nueva:
                        nuevos += 1
                    else:
                        actualizados += 1
                except Exception as exc:
                    errores += 1
                    log_lines.append(f'Error item: {exc}')

            ejecucion.estado = 'completado' if not item.get('error') else 'error'
        except Exception:
            ejecucion.estado = 'error'
            errores += 1
            log_lines.append(traceback.format_exc())

        ejecucion.encontrados = encontrados
        ejecucion.nuevos = nuevos
        ejecucion.actualizados = actualizados
        ejecucion.errores = errores
        ejecucion.log = '\n'.join(log_lines)
        ejecucion.finalizado_en = timezone.now()
        ejecucion.save()

        return {
            'fuente': fuente.nombre, 'encontrados': encontrados,
            'nuevos': nuevos, 'actualizados': actualizados,
            'errores': errores, 'estado': ejecucion.estado, 'motor': motor,
        }

    @classmethod
    def importar_url(cls, url, zona_id, usuario=None):
        raw = None
        scraper = None

        if cls._usar_playwright():
            from services.scraping.playwright_fetcher import PlaywrightSession
            with PlaywrightSession() as pw_session:
                scraper = obtener_scraper_por_url(url, playwright_session=pw_session)
                if scraper:
                    raw = scraper.parse_detalle_url(url)
        else:
            scraper = obtener_scraper_por_url(url)
            if scraper:
                raw = scraper.parse_detalle_url(url)

        if not scraper or not raw:
            raise ValueError(
                'URL no soportada. Portales: Mercado Libre, Lamudi, Propiedades.com, Vivanuncios, Inmuebles24.'
            )

        normalizado = normalizar_listing(raw, zona_id)
        if not normalizado:
            raise ValueError('No se pudo extraer precio o datos mínimos de la URL.')

        fuente = scraper.fuente
        if not fuente.pk:
            fuente, _ = FuenteDatos.objects.get_or_create(
                nombre=scraper.fuente_nombre,
                defaults={'tipo': 'portal', 'activa': True, 'url_base': scraper.base_url},
            )

        normalizado['descripcion'] = normalizado.get('descripcion') or 'Importada desde URL (Playwright)'
        return registrar_desde_fuente(normalizado, fuente, capturado_por=usuario)