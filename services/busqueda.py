"""Servicio de búsqueda semanal — Casa Verde (Fase 4)."""
import logging
from datetime import date

from django.utils import timezone

from analisis.models import ConfiguracionBusqueda
from propiedades.models import Propiedad
from services.oportunidad import OportunidadService
from services.registro import registrar_desde_fuente

logger = logging.getLogger(__name__)


class BusquedaService:
    """Orquesta scraping + re-análisis de propiedades por zona."""

    @classmethod
    def ejecutar_todas(cls):
        configs = ConfiguracionBusqueda.objects.filter(activa=True).select_related(
            'usuario', 'zona', 'zona__municipio',
        )
        return [cls.ejecutar_configuracion(c) for c in configs]

    @classmethod
    def ejecutar_configuracion(cls, config):
        zona = config.zona
        logger.info('Búsqueda en %s — usuario %s', zona.nombre, config.usuario.username)

        from services.scraping import ScrapingService
        scrape_resumen = ScrapingService.ejecutar_para_config(config)

        propiedades = Propiedad.objects.filter(zona=zona)
        if config.tipo_inmueble:
            propiedades = propiedades.filter(tipo_inmueble=config.tipo_inmueble)

        reanalizadas = 0
        oportunidades = 0
        for propiedad in propiedades:
            analisis = OportunidadService.analizar_propiedad(propiedad, usuario=config.usuario)
            reanalizadas += 1
            if analisis.es_oportunidad:
                oportunidades += 1

        config.ultima_ejecucion = timezone.now()
        config.save(update_fields=['ultima_ejecucion'])

        return {
            'zona': zona.nombre,
            'usuario': config.usuario.username,
            'scrape': scrape_resumen,
            'propiedades_reanalizadas': reanalizadas,
            'oportunidades': oportunidades,
            'fecha': date.today().isoformat(),
        }

    registrar_desde_fuente = staticmethod(registrar_desde_fuente)