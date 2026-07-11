"""
Punto de entrada para Passenger (cPanel → Setup Python App).

Passenger busca una variable llamada `application` en este archivo.
Reutilizamos la aplicación WSGI de Django definida en config/wsgi.py,
que ya fija DJANGO_SETTINGS_MODULE=config.settings.
"""
from config.wsgi import application  # noqa: F401
