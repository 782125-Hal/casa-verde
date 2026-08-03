from django.apps import AppConfig


class PresupuestosConfig(AppConfig):
    name = "presupuestos"
    verbose_name = "Presupuestos de obra"

    def ready(self):
        # Registra las señales que recalculan el ROI (Fase 3). Import dentro de
        # ready() porque a nivel de módulo las apps aún no están cargadas.
        from presupuestos import signals  # noqa: F401
