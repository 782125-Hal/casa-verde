"""Normalización de datos extraídos por scrapers."""
import re
from decimal import Decimal, InvalidOperation

from core.choices import TIPO_INMUEBLE_CHOICES


def limpiar_texto(texto):
    if not texto:
        return ''
    return re.sub(r'\s+', ' ', str(texto)).strip()


def parse_precio(texto):
    if not texto:
        return None
    limpio = re.sub(r'[^\d.]', '', str(texto).replace(',', ''))
    if not limpio:
        return None
    try:
        valor = Decimal(limpio)
        if valor > 0:
            return valor.quantize(Decimal('0.01'))
    except InvalidOperation:
        return None
    return None


def parse_metros(texto):
    if not texto:
        return None
    match = re.search(r'([\d,.]+)\s*m[²2]', str(texto), re.I)
    if match:
        num = match.group(1).replace(',', '')
        try:
            return Decimal(num).quantize(Decimal('0.01'))
        except InvalidOperation:
            return None
    return None


def detectar_tipo_inmueble(titulo, descripcion=''):
    texto = f'{titulo} {descripcion}'.lower()
    reglas = [
        ('terreno', ['terreno', 'lote', 'parcela']),
        ('departamento', ['departamento', 'depto', 'depa', 'condominio vertical']),
        ('local', ['local comercial', 'local ', 'bodega comercial', 'plaza comercial']),
        ('nave', ['nave industrial', 'bodega industrial', 'nave ']),
        ('casa', ['casa', 'residencia', 'chalet', 'vivienda']),
    ]
    for tipo, palabras in reglas:
        if any(p in texto for p in palabras):
            return tipo
    return 'otro'


def validar_tipo(tipo):
    validos = {t[0] for t in TIPO_INMUEBLE_CHOICES}
    return tipo if tipo in validos else 'otro'


def normalizar_listing(raw, zona_id):
    """Convierte dict crudo del scraper al formato de Propiedad."""
    titulo = limpiar_texto(raw.get('titulo')) or 'Propiedad detectada'
    descripcion = limpiar_texto(raw.get('descripcion'))
    tipo = validar_tipo(raw.get('tipo_inmueble') or detectar_tipo_inmueble(titulo, descripcion))

    precio = raw.get('precio_publicado')
    if not isinstance(precio, Decimal):
        precio = parse_precio(raw.get('precio_texto') or precio)

    m2_terreno = raw.get('m2_terreno')
    m2_construccion = raw.get('m2_construccion')
    if not m2_terreno:
        m2_terreno = parse_metros(raw.get('superficie_texto') or descripcion)
    if not m2_construccion and tipo != 'terreno':
        m2_construccion = parse_metros(raw.get('construccion_texto') or '')

    url = limpiar_texto(raw.get('url_anuncio'))
    if not url or not precio:
        return None

    return {
        'titulo': titulo[:300],
        'descripcion': descripcion[:5000],
        'precio_publicado': precio,
        'zona_id': zona_id,
        'tipo_inmueble': tipo,
        'm2_terreno': m2_terreno,
        'm2_construccion': m2_construccion,
        'url_anuncio': url[:500],
        'imagen_url': limpiar_texto(raw.get('imagen_url'))[:500],
        'direccion': limpiar_texto(raw.get('direccion'))[:400],
        'estado_fisico': 'regular',
        'descripcion_sistema': 'Detectada automáticamente por Casa Verde',
    }