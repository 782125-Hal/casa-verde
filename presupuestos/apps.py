# El servidor corre Python 3.9: sin esto, una anotación como `Decimal | None`
# se evalúa al importar y truena con "unsupported operand type(s) for |".
from __future__ import annotations

from django.apps import AppConfig


class PresupuestosConfig(AppConfig):
    name = "presupuestos"
    verbose_name = "Presupuestos de obra"

    def ready(self):
        # Registra las señales que recalculan el ROI (Fase 3). Import dentro de
        # ready() porque a nivel de módulo las apps aún no están cargadas.
        from presupuestos import signals  # noqa: F401
