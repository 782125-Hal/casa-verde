"""Tareas Celery — búsqueda semanal."""
from celery import shared_task

from services.busqueda import BusquedaService


@shared_task(name='analisis.tasks.ejecutar_busqueda_semanal')
def ejecutar_busqueda_semanal():
    resultados = BusquedaService.ejecutar_todas()
    return {
        'configs_procesadas': len(resultados),
        'zonas': [r['zona'] for r in resultados],
    }