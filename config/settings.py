from pathlib import Path

from decouple import Config, Csv, RepositoryEnv

BASE_DIR = Path(__file__).resolve().parent.parent

_env_path = BASE_DIR / '.env'
config = Config(RepositoryEnv(_env_path)) if _env_path.exists() else Config()

SECRET_KEY = config(
    'SECRET_KEY',
    default='django-insecure-casa-verde-dev-key-change-in-production',
)

DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

# Orígenes de confianza para CSRF (necesario para el admin/formularios sobre
# HTTPS en un dominio propio). Ej: https://casaverde.marhal.com.mx
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='', cast=Csv())

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'core',
    'usuarios',
    'geografia',
    'mercado',
    'propiedades.apps.PropiedadesConfig',
    'analisis',
    'alertas',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise sirve los archivos estáticos en producción sin servidor extra.
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.casa_verde_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_USER_MODEL = 'usuarios.Usuario'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-mx'
TIME_ZONE = 'America/Monterrey'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
# Carpeta donde `collectstatic` junta los estáticos para producción.
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Almacenamiento de estáticos: en producción usa WhiteNoise (comprimido).
if not DEBUG:
    STORAGES = {
        'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
        'staticfiles': {
            'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
        },
    }

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# --- Seguridad en producción (activa solo cuando DEBUG=False) ---
if not DEBUG:
    # cPanel/Passenger y la mayoría de hosts ponen un proxy con HTTPS al frente.
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    # Redirección a HTTPS: controlable por variable para evitar bucles si el
    # host ya fuerza HTTPS. Actívala con SECURE_SSL_REDIRECT=True en el .env.
    SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/admin/login/'
LOGIN_REDIRECT_URL = '/'

# Casa Verde — parámetros globales
# Celery (opcional — Fase 4 producción)
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True

# Scraping — Fase 4 Playwright
SCRAPING_USE_PLAYWRIGHT = True
SCRAPING_PLAYWRIGHT_HEADLESS = True
SCRAPING_PLAYWRIGHT_WAIT_MS = 3000
SCRAPING_PLAYWRIGHT_TIMEOUT = 45000
SCRAPING_PLAYWRIGHT_RATE_LIMIT = 3.0
SCRAPING_RESPECT_ROBOTS = True

# Alertas — Fase 5 (credenciales en .env)
# Desarrollo: consola. Producción: EMAIL_BACKEND=smtp + credenciales SMTP.
EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.console.EmailBackend',
)
DEFAULT_FROM_EMAIL = config(
    'DEFAULT_FROM_EMAIL',
    default='Casa Verde <alertas@casaverde.local>',
)
EMAIL_HOST = config('EMAIL_HOST', default='')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')

# Telegram: bot con @BotFather → TELEGRAM_BOT_TOKEN en .env
TELEGRAM_BOT_TOKEN = config('TELEGRAM_BOT_TOKEN', default='')

CASA_VERDE = {
    'NOMBRE': 'Casa Verde',
    'CIUDAD_DEFAULT': 'Tijuana',
    'ESTADO_DEFAULT': 'Baja California',
    'ZONAS_PRIORITARIAS': ['La Mesa', 'Las Palmas', 'Zona Río'],
    'DESCUENTO_MINIMO_DEFAULT': 15.0,
    'PLAZO_RECUPERACION_DEFAULT': 3,
    'TASA_BANCARIA_DEFAULT': 4.5,
}