"""Pruebas de core.

Hoy solo cubren `check_39`, el guardián de compatibilidad con el Python del
hosting. Se corre desde la suite para que la incompatibilidad se detecte al
hacer `manage.py test` y no al desplegar.
"""

# El servidor corre Python 3.9: sin esto, una anotación como `Decimal | None`
# se evalúa al importar y truena con "unsupported operand type(s) for |".
from __future__ import annotations

import pathlib
import tempfile
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase


class Check39Test(SimpleTestCase):
    """El proyecto debe seguir arrancando en el Python 3.9 del cPanel."""

    def _correr(self, ruta=None):
        salida = StringIO()
        argumentos = [ruta] if ruta else []
        call_command('check_39', *argumentos, stdout=salida, stderr=salida)
        return salida.getvalue()

    def _archivo_temporal(self, nombre, fuente):
        carpeta = tempfile.mkdtemp()
        ruta = pathlib.Path(carpeta) / nombre
        ruta.write_text(fuente, encoding='utf-8')
        self.addCleanup(lambda: (ruta.unlink(missing_ok=True),
                                 pathlib.Path(carpeta).rmdir()))
        return str(ruta)

    def test_el_proyecto_es_compatible_con_39(self):
        """La prueba de regresión: nadie vuelve a meter sintaxis de 3.10+."""
        salida = self._correr()
        self.assertIn('Sin incompatibilidades', salida)

    def test_detecta_anotacion_sin_import_del_futuro(self):
        """Exactamente el error que tumbó el módulo de presupuestos en el servidor."""
        ruta = self._archivo_temporal('anotacion.py', 'def f() -> int | None:\n    return 1\n')
        with self.assertRaises(CommandError):
            self._correr(ruta)

    def test_el_import_del_futuro_silencia_las_anotaciones(self):
        """Con el import, la anotación nunca se evalúa: en 3.9 da igual."""
        ruta = self._archivo_temporal(
            'con_futuro.py',
            'from __future__ import annotations\n\n\ndef f() -> int | None:\n    return 1\n')
        self.assertIn('Sin incompatibilidades', self._correr(ruta))

    def test_detecta_el_pipe_de_runtime_pese_al_import(self):
        """El import NO salva un `|` que se evalúa: eso hay que reescribirlo."""
        ruta = self._archivo_temporal(
            'runtime.py',
            'from __future__ import annotations\n\n\n'
            'def f(x):\n    return isinstance(x, int | str)\n')
        with self.assertRaises(CommandError):
            self._correr(ruta)

    def test_detecta_match_case(self):
        ruta = self._archivo_temporal(
            'match.py',
            'def f(x):\n    match x:\n        case 1:\n            return 1\n')
        with self.assertRaises(CommandError):
            self._correr(ruta)

    def test_no_se_queja_del_pipe_legitimo(self):
        """Un `|` de ORM, de conjuntos o de bits no es una anotación."""
        ruta = self._archivo_temporal(
            'legitimo.py',
            'from __future__ import annotations\n\n\n'
            'def f(a, b):\n    return (a | b, {1} | {2}, 0b01 | 0b10)\n')
        self.assertIn('Sin incompatibilidades', self._correr(ruta))
