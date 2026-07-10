"""
Configuración Celery para búsqueda semanal automatizada.
Activar en producción: pip install celery redis
"""
import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('casa_verde')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Búsqueda semanal: lunes 7:00 AM (America/Tijuana)
app.conf.beat_schedule = {
    'busqueda-semanal-tijuana': {
        'task': 'analisis.tasks.ejecutar_busqueda_semanal',
        'schedule': crontab(hour=7, minute=0, day_of_week=1),
    },
}