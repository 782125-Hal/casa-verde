"""
Punto de entrada para Passenger (cPanel → Setup Python App).

Passenger busca una variable llamada `application` en este archivo.
Reutilizamos la aplicación WSGI de Django definida en config/wsgi.py,
que ya fija DJANGO_SETTINGS_MODULE=config.settings.

Nota: NO cargar este archivo con imp.load_source('...', 'passenger_wsgi.py')
(la plantilla por defecto de cPanel hace eso y provoca recursión infinita).
Este archivo importa Django directamente, sin auto-referencia.
"""
import os
import sys

# Asegura que el directorio de la app esté en el path para importar `config`.
sys.path.insert(0, os.path.dirname(__file__))

from config.wsgi import application  # noqa: E402,F401
