"""Detecta sintaxis que el hosting (Python 3.9) no acepta.

Existe porque el venv de desarrollo es 3.12 y el servidor cPanel es 3.9: cinco
fases del módulo de presupuestos se escribieron y se dieron por buenas en local
con una anotación `Decimal | None` que en 3.9 revienta al importar. `manage.py
check` no lo ve, porque para Django el código es válido; lo que falla es la
versión del intérprete.

Uso:
    python manage.py check_39                 # todo el proyecto
    python manage.py check_39 presupuestos    # solo esa carpeta
    python manage.py check_39 -v 2            # lista además los archivos leídos

Termina con código distinto de cero si encuentra algo, para poder colgarlo de CI
o de un hook de pre-deploy.

Sobre el enfoque
----------------
Se analiza el árbol sintáctico, no se hace grep. La diferencia importa porque
`|` en una anotación y `|` en un `isinstance` se arreglan de formas distintas, y
un grep no puede distinguirlos: el primero lo cubre `from __future__ import
annotations`, que difiere la evaluación de las anotaciones del módulo; el
segundo se evalúa siempre y hay que reescribirlo con `Optional`/`Union` o con
una tupla.

Se prefiere callar antes que dar un falso positivo. Un `x = a | b` entre nombres
sueltos puede ser una unión de conjuntos o un OR de enteros tanto como un alias
de tipo, así que solo se señala cuando uno de los lados es `None`, que no admite
otra lectura. El precio es que un alias como `Numero = int | float` pasa
inadvertido; a cambio, cuando este comando se queja, se queja de algo real.
"""

# El servidor corre Python 3.9: sin esto, una anotación como `Decimal | None`
# se evalúa al importar y truena con "unsupported operand type(s) for |".
from __future__ import annotations

import ast
import pathlib
import sys

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

DESTINO = (3, 9)

CARPETAS_IGNORADAS = frozenset({
    'venv', '.venv', 'env', '__pycache__', 'node_modules',
    'staticfiles', 'media', '.git', '.tox', 'build', 'dist',
})

FUNCIONES_QUE_EVALUAN = frozenset({'isinstance', 'issubclass', 'cast', 'get_type_hints'})

# Nombres que no existen en 3.9. Solo los de importación explícita, que son los
# que se detectan sin ambigüedad.
MODULOS_NUEVOS = {'tomllib': '3.11', 'graphlib': '3.9+'}
MIEMBROS_NUEVOS = {
    'typing': {
        'TypeAlias': '3.10', 'TypeGuard': '3.10', 'ParamSpec': '3.10',
        'Concatenate': '3.10', 'Self': '3.11', 'Never': '3.11',
        'LiteralString': '3.11', 'assert_type': '3.11', 'reveal_type': '3.11',
        'override': '3.12', 'TypeAliasType': '3.12',
    },
    'itertools': {'pairwise': '3.10', 'batched': '3.12'},
    'asyncio': {'TaskGroup': '3.11', 'Barrier': '3.11', 'timeout': '3.11'},
    'enum': {'StrEnum': '3.11', 'ReprEnum': '3.11', 'verify': '3.11'},
    'datetime': {'UTC': '3.11'},
    'inspect': {'get_annotations': '3.10'},
}
BUILTINS_NUEVOS = {'ExceptionGroup': '3.11', 'BaseExceptionGroup': '3.11', 'aiter': '3.10', 'anext': '3.10'}

# (función, keyword) que solo existen a partir de 3.10.
KWARGS_NUEVOS = {('zip', 'strict'): '3.10', ('dataclass', 'slots'): '3.10',
                 ('dataclass', 'kw_only'): '3.10', ('dataclass', 'match_args'): '3.10'}

# Severidad: los 'error' rompen el arranque; los 'aviso' solo si se ejecuta esa línea.
ERROR, AVISO = 'error', 'aviso'


class Hallazgo:
    __slots__ = ('ruta', 'linea', 'categoria', 'detalle', 'severidad', 'arreglo')

    def __init__(self, ruta, linea, categoria, detalle, severidad, arreglo):
        self.ruta = ruta
        self.linea = linea
        self.categoria = categoria
        self.detalle = detalle
        self.severidad = severidad
        self.arreglo = arreglo


def _hay_bitor(nodo) -> bool:
    """¿Aparece un `|` en algún punto de este subárbol?"""
    return any(isinstance(n, ast.BinOp) and isinstance(n.op, ast.BitOr)
               for n in ast.walk(nodo))


def _menciona_none(nodo) -> bool:
    """¿Alguno de los operandos es `None`? Delata un tipo opcional."""
    return any(isinstance(n, ast.Constant) and n.value is None for n in ast.walk(nodo))


def _nombre_llamada(nodo: ast.Call):
    f = nodo.func
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute):
        return f.attr
    return None


class Analizador(ast.NodeVisitor):
    """Recorre un módulo y anota lo que 3.9 no soportaría."""

    def __init__(self, ruta, tiene_futuro):
        self.ruta = ruta
        self.tiene_futuro = tiene_futuro
        self.hallazgos = []
        self._alias_import = {}   # nombre local -> módulo de origen

    def _añadir(self, linea, categoria, detalle, severidad, arreglo):
        self.hallazgos.append(
            Hallazgo(self.ruta, linea, categoria, detalle, severidad, arreglo))

    # --- anotaciones: las salva el import del futuro ------------------------

    def _revisar_anotacion(self, nodo, contexto):
        if nodo is None or not _hay_bitor(nodo):
            return
        if self.tiene_futuro:
            return  # perezosa: nunca se evalúa, así que en 3.9 da igual
        self._añadir(
            nodo.lineno, 'anotación',
            f'{contexto}: usa `|` (PEP 604, 3.10+)', ERROR,
            'añade `from __future__ import annotations` tras el docstring')

    def visit_FunctionDef(self, nodo):
        self._revisar_anotacion(nodo.returns, f'retorno de {nodo.name}()')
        a = nodo.args
        for arg in (*a.posonlyargs, *a.args, *a.kwonlyargs, a.vararg, a.kwarg):
            if arg is not None:
                self._revisar_anotacion(
                    arg.annotation, f'parámetro `{arg.arg}` de {nodo.name}()')
        self._revisar_type_params(nodo, f'{nodo.name}()')
        self.generic_visit(nodo)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, nodo):
        self._revisar_type_params(nodo, f'class {nodo.name}')
        self.generic_visit(nodo)

    def _revisar_type_params(self, nodo, contexto):
        # `def f[T]()` / `class C[T]` — sintaxis de 3.12.
        if getattr(nodo, 'type_params', None):
            self._añadir(nodo.lineno, 'sintaxis',
                         f'{contexto}: parámetros de tipo en corchetes (3.12)',
                         ERROR, 'usa TypeVar del módulo typing')

    def visit_AnnAssign(self, nodo):
        self._revisar_anotacion(nodo.annotation, 'anotación de variable')
        # El VALOR sí se evalúa aunque haya import del futuro.
        if nodo.value is not None and _hay_bitor(nodo.value):
            self._añadir(
                nodo.lineno, 'runtime',
                'alias de tipo con `|` en el valor asignado', ERROR,
                'usa typing.Optional o typing.Union')
        self.generic_visit(nodo)

    # --- runtime: el import del futuro NO las arregla -----------------------

    def visit_Assign(self, nodo):
        if _hay_bitor(nodo.value) and _menciona_none(nodo.value):
            self._añadir(
                nodo.lineno, 'runtime',
                'asignación de un tipo opcional con `X | None`', ERROR,
                'usa typing.Optional[X]')
        self.generic_visit(nodo)

    def visit_Call(self, nodo):
        nombre = _nombre_llamada(nodo)

        if nombre in FUNCIONES_QUE_EVALUAN:
            for arg in nodo.args:
                if _hay_bitor(arg):
                    arreglo = ('usa una tupla: isinstance(x, (A, B))'
                               if nombre in ('isinstance', 'issubclass')
                               else 'usa typing.Optional o typing.Union')
                    self._añadir(nodo.lineno, 'runtime',
                                 f'{nombre}() recibe un `|` que se evalúa siempre',
                                 ERROR, arreglo)
            if nombre == 'get_type_hints':
                self._añadir(
                    nodo.lineno, 'runtime',
                    'get_type_hints() fuerza la evaluación de las anotaciones, '
                    'anulando el efecto de `from __future__ import annotations`',
                    AVISO, 'revisa que ningún módulo alcanzado use `|` en anotaciones')

        for kw in nodo.keywords:
            version = KWARGS_NUEVOS.get((nombre, kw.arg))
            if version:
                self._añadir(nodo.lineno, 'stdlib',
                             f'{nombre}(..., {kw.arg}=...) existe desde {version}',
                             ERROR, 'elimina ese argumento o replica su efecto a mano')

        self.generic_visit(nodo)

    # --- sintaxis y stdlib --------------------------------------------------

    def visit_Match(self, nodo):
        self._añadir(nodo.lineno, 'sintaxis', 'match/case (3.10)', ERROR,
                     'reescríbelo con if/elif')
        self.generic_visit(nodo)

    def visit_TryStar(self, nodo):  # pragma: no cover - solo si alguien lo escribe
        self._añadir(nodo.lineno, 'sintaxis', 'except* (3.11)', ERROR,
                     'usa un except normal')
        self.generic_visit(nodo)

    def visit_TypeAlias(self, nodo):  # pragma: no cover
        self._añadir(nodo.lineno, 'sintaxis', 'sentencia `type X = ...` (3.12)',
                     ERROR, 'asigna el alias normalmente')
        self.generic_visit(nodo)

    def visit_Import(self, nodo):
        for alias in nodo.names:
            raiz = alias.name.split('.')[0]
            if raiz in MODULOS_NUEVOS:
                self._añadir(nodo.lineno, 'stdlib',
                             f'el módulo `{raiz}` existe desde {MODULOS_NUEVOS[raiz]}',
                             ERROR, 'busca un equivalente disponible en 3.9')
            self._alias_import[alias.asname or raiz] = raiz
        self.generic_visit(nodo)

    def visit_ImportFrom(self, nodo):
        modulo = nodo.module or ''
        if modulo.split('.')[0] in MODULOS_NUEVOS:
            self._añadir(
                nodo.lineno, 'stdlib',
                f'el módulo `{modulo}` existe desde {MODULOS_NUEVOS[modulo.split(".")[0]]}',
                ERROR, 'busca un equivalente disponible en 3.9')
        nuevos = MIEMBROS_NUEVOS.get(modulo, {})
        for alias in nodo.names:
            version = nuevos.get(alias.name)
            if version:
                self._añadir(
                    nodo.lineno, 'stdlib',
                    f'`{modulo}.{alias.name}` existe desde {version}', ERROR,
                    'usa typing_extensions o un equivalente de 3.9')
        self.generic_visit(nodo)

    def visit_Name(self, nodo):
        if isinstance(nodo.ctx, ast.Load) and nodo.id in BUILTINS_NUEVOS:
            self._añadir(nodo.lineno, 'stdlib',
                         f'`{nodo.id}` existe desde {BUILTINS_NUEVOS[nodo.id]}',
                         ERROR, 'usa un equivalente disponible en 3.9')
        self.generic_visit(nodo)


def _tiene_import_del_futuro(arbol) -> bool:
    return any(
        isinstance(n, ast.ImportFrom) and n.module == '__future__'
        and any(a.name == 'annotations' for a in n.names)
        for n in arbol.body
    )


def analizar_archivo(ruta: pathlib.Path, mostrado: str):
    """Analiza un módulo y devuelve sus hallazgos."""
    try:
        fuente = ruta.read_text(encoding='utf-8')
    except (UnicodeDecodeError, OSError) as exc:
        return [Hallazgo(mostrado, 0, 'lectura', f'no se pudo leer: {exc}',
                         AVISO, 'revísalo a mano')]

    try:
        arbol = ast.parse(fuente, filename=str(ruta))
    except SyntaxError as exc:
        # Corriendo ya bajo 3.9 esto es la prueba directa: no compila.
        return [Hallazgo(mostrado, exc.lineno or 0, 'sintaxis',
                         f'no compila: {exc.msg}', ERROR,
                         'reescríbelo con sintaxis de 3.9')]

    analizador = Analizador(mostrado, _tiene_import_del_futuro(arbol))
    analizador.visit(arbol)
    return analizador.hallazgos


def recolectar(raiz: pathlib.Path):
    """Módulos del proyecto, saltando entornos virtuales y artefactos."""
    for ruta in sorted(raiz.rglob('*.py')):
        if CARPETAS_IGNORADAS.intersection(ruta.parts):
            continue
        yield ruta


class Command(BaseCommand):
    help = 'Detecta sintaxis incompatible con Python 3.9 (la versión del hosting).'

    def add_arguments(self, parser):
        parser.add_argument(
            'ruta', nargs='?', default=None,
            help='Carpeta o archivo a revisar. Por omisión, todo el proyecto.')
        parser.add_argument(
            '--incluir-avisos', action='store_true',
            help='Trata los avisos como fallo, no solo los errores.')

    def handle(self, *args, **opciones):
        verbosidad = opciones['verbosity']
        base = pathlib.Path(settings.BASE_DIR)
        objetivo = pathlib.Path(opciones['ruta']) if opciones['ruta'] else base
        if not objetivo.is_absolute():
            objetivo = base / objetivo
        if not objetivo.exists():
            raise CommandError(f'No existe: {objetivo}')

        archivos = [objetivo] if objetivo.is_file() else list(recolectar(objetivo))

        hallazgos = []
        for ruta in archivos:
            try:
                mostrado = str(ruta.relative_to(base))
            except ValueError:
                mostrado = str(ruta)
            encontrados = analizar_archivo(ruta, mostrado)
            hallazgos.extend(encontrados)
            if verbosidad >= 2:
                marca = self.style.ERROR('x') if encontrados else self.style.SUCCESS('.')
                self.stdout.write(f'  {marca} {mostrado}')

        corriendo = '.'.join(str(n) for n in sys.version_info[:3])
        destino = '.'.join(str(n) for n in DESTINO)
        errores = [h for h in hallazgos if h.severidad == ERROR]
        avisos = [h for h in hallazgos if h.severidad == AVISO]

        if verbosidad >= 1:
            self.stdout.write('')
            self.stdout.write(
                f'Revisados {len(archivos)} módulos contra Python {destino} '
                f'(este intérprete es {corriendo}).')

        self._reportar(errores, 'INCOMPATIBLE con 3.9', self.style.ERROR, verbosidad)
        self._reportar(avisos, 'Avisos', self.style.WARNING, verbosidad)

        if errores:
            raise CommandError(
                f'{len(errores)} problema(s) que impiden correr en Python {destino}.')
        if avisos and opciones['incluir_avisos']:
            raise CommandError(f'{len(avisos)} aviso(s), y se pidió tratarlos como fallo.')

        if verbosidad >= 1:
            extra = f' ({len(avisos)} aviso(s))' if avisos else ''
            self.stdout.write(self.style.SUCCESS(
                f'Sin incompatibilidades con Python {destino}.{extra}'))

    def _reportar(self, hallazgos, titulo, estilo, verbosidad):
        if not hallazgos or verbosidad < 1:
            return
        self.stdout.write('')
        self.stdout.write(estilo(f'{titulo} ({len(hallazgos)}):'))
        for h in sorted(hallazgos, key=lambda x: (x.ruta, x.linea)):
            self.stdout.write(f'  {h.ruta}:{h.linea}  [{h.categoria}] {h.detalle}')
            self.stdout.write(f'      → {h.arreglo}')
