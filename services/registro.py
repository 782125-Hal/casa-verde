"""Registro y deduplicación de propiedades desde fuentes externas."""
from propiedades.models import Propiedad


def registrar_desde_fuente(datos, fuente, capturado_por=None):
    datos = dict(datos)
    zona_id = datos.pop('zona_id')
    url = datos.get('url_anuncio', '')

    existente = Propiedad.objects.filter(url_anuncio=url).first() if url else None

    if existente:
        cambio = False
        if datos.get('precio_publicado') and existente.precio_publicado != datos['precio_publicado']:
            existente.precio_publicado = datos['precio_publicado']
            cambio = True
        for campo in ('titulo', 'descripcion', 'm2_terreno', 'm2_construccion', 'imagen_url'):
            if datos.get(campo) and getattr(existente, campo) != datos[campo]:
                setattr(existente, campo, datos[campo])
                cambio = True
        if cambio:
            existente.save()
        return existente, False

    propiedad = Propiedad.objects.create(
        zona_id=zona_id,
        fuente=fuente,
        capturado_por=capturado_por,
        **datos,
    )
    return propiedad, True