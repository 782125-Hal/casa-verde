"""Filtro geográfico para listados scrapeados — Tijuana por zona."""
import re
import unicodedata

# Palabras que indican que el inmueble NO está en el área de interés
EXCLUIR_GLOBAL = [
    'la paz', 'mexicali', 'ensenada', 'tecate', 'rosarito', 'san quintin',
    'san felipe', 'valle de guadalupe', 'baja california sur', 'los cabos',
    'culiacán', 'culiacan', 'monterrey', 'cdmx', 'ciudad de méxico',
]

ZONA_FILTROS = {
    'La Mesa': {
        'incluir': [
            'la mesa', 'colonia la mesa', 'cuauhtémoc', 'cuauhtemoc',
            'alamar', 'camino verde', 'el lago', 'villa del campo',
            'sánchez taboada', 'sanchez taboada', 'blvd salinas',
        ],
        'excluir': ['otay', 'playas de tijuana', 'playas', 'zona rio', 'zona río',
                    'garita de otay', 'centro tijuana', 'las palmas', 'chapultepec'],
    },
    'Las Palmas': {
        'incluir': [
            'las palmas', 'colonia las palmas', 'chapultepec', 'hipódromo',
            'hipodromo', 'cumbres', 'jardines', 'aguacaliente',
        ],
        'excluir': ['otay', 'playas', 'zona rio', 'zona río', 'la mesa', 'centro',
                    'garita', 'la paz', 'otay universidad'],
    },
    'Zona Río': {
        'incluir': [
            'zona rio', 'zona río', 'zona urbana rio', 'zona urbana río',
            'sánchez taboada', 'sanchez taboada', 'paseo de los héroes',
            'paseo de los heroes', 'rio tijuana', 'río tijuana', 'cuitláhuac',
        ],
        'excluir': ['otay', 'playas', 'la mesa', 'las palmas', 'centro', 'la paz',
                    'garita de otay', 'otay universidad'],
    },
    'Playas de Tijuana': {
        'incluir': [
            'playas de tijuana', 'playas', 'sección jardines', 'seccion jardines',
            'costa de oro', 'paseo de la victoria', 'corona del mar',
        ],
        'excluir': ['otay', 'la mesa', 'zona rio', 'zona río', 'centro', 'las palmas', 'la paz'],
    },
    'Otay': {
        'incluir': [
            'otay', 'garita de otay', 'otay universidad', 'otay constituyentes',
            'ciudad industrial', 'mesa de otay', 'el florido', 'santa fe',
        ],
        'excluir': ['la mesa', 'playas', 'zona rio', 'zona río', 'centro',
                    'las palmas', 'la paz', 'la juárez'],
    },
    'Centro': {
        'incluir': [
            'centro', 'zona centro', 'revolución', 'revolucion', 'artículo 123',
            'articulo 123', 'marron', 'marrón', 'aviación', 'aviacion',
        ],
        'excluir': ['otay', 'playas', 'la mesa', 'zona rio', 'zona río',
                    'las palmas', 'la paz', 'otay universidad'],
    },
}


def _normalizar(texto):
    if not texto:
        return ''
    texto = texto.lower().strip()
    texto = ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )
    return re.sub(r'\s+', ' ', texto)


def pertenece_a_zona(titulo, zona_nombre, direccion='', descripcion='', colonia=''):
    """
    Retorna True si el listado parece estar en la zona configurada.
    Modo estricto: rechaza si detecta otra zona/ciudad.
    """
    texto = _normalizar(f'{titulo} {direccion} {descripcion} {colonia}')

    if not texto:
        return False

    for termino in EXCLUIR_GLOBAL:
        if termino in texto:
            return False

    filtros = ZONA_FILTROS.get(zona_nombre, {})
    zona_norm = _normalizar(zona_nombre)
    colonia_norm = _normalizar(colonia)

    for termino in filtros.get('excluir', []):
        if _normalizar(termino) in texto:
            return False

    for termino in filtros.get('incluir', []):
        if _normalizar(termino) in texto:
            return True

    if zona_norm in texto:
        return True

    if colonia_norm and colonia_norm in texto:
        return True

    return False


def filtrar_listados(listados, zona):
    """Filtra lista de dicts crudos del scraper."""
    filtrados = []
    rechazados = 0
    for item in listados:
        if pertenece_a_zona(
            titulo=item.get('titulo', ''),
            zona_nombre=zona.nombre,
            direccion=item.get('direccion', ''),
            descripcion=item.get('descripcion', ''),
            colonia=zona.colonia,
        ):
            filtrados.append(item)
        else:
            rechazados += 1
    return filtrados, rechazados