from django.apps import AppConfig


class PropiedadesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'propiedades'
    verbose_name = 'Propiedades'

    def ready(self):
        import propiedades.signals  # noqa: F401