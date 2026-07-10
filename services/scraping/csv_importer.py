"""Importación masiva CSV — alternativa cuando portales bloquean scraping."""
import csv
import io
from decimal import Decimal

from mercado.models import FuenteDatos
from services.registro import registrar_desde_fuente
from services.scraping.normalizer import detectar_tipo_inmueble, parse_metros, parse_precio, validar_tipo


class CSVImporter:
    COLUMNAS = {
        'titulo': ['titulo', 'title', 'nombre'],
        'precio': ['precio', 'price', 'precio_publicado'],
        'zona': ['zona', 'colonia', 'ubicacion'],
        'tipo': ['tipo', 'tipo_inmueble', 'type'],
        'm2_terreno': ['m2_terreno', 'terreno', 'superficie_terreno'],
        'm2_construccion': ['m2_construccion', 'construccion', 'superficie_construccion'],
        'url': ['url', 'url_anuncio', 'enlace', 'link'],
        'direccion': ['direccion', 'address'],
        'descripcion': ['descripcion', 'description'],
    }

    @classmethod
    def _mapear_columnas(cls, headers):
        headers_lower = [h.lower().strip() for h in headers]
        mapping = {}
        for campo, aliases in cls.COLUMNAS.items():
            for alias in aliases:
                if alias in headers_lower:
                    mapping[campo] = headers_lower.index(alias)
                    break
        return mapping

    @classmethod
    def importar(cls, archivo, zonas_por_nombre, usuario=None):
        contenido = archivo.read().decode('utf-8-sig')
        reader = csv.reader(io.StringIO(contenido))
        rows = list(reader)
        if len(rows) < 2:
            raise ValueError('El CSV debe tener encabezado y al menos una fila.')

        mapping = cls._mapear_columnas(rows[0])
        if 'titulo' not in mapping or 'precio' not in mapping:
            raise ValueError('CSV requiere columnas: titulo, precio (y opcionalmente zona, tipo, url).')

        fuente, _ = FuenteDatos.objects.get_or_create(
            nombre='Importación CSV',
            defaults={'tipo': 'manual', 'activa': True},
        )

        nuevos = actualizados = errores = 0
        for row in rows[1:]:
            try:
                titulo = row[mapping['titulo']].strip()
                precio = parse_precio(row[mapping['precio']])
                if not titulo or not precio:
                    errores += 1
                    continue

                zona = None
                if 'zona' in mapping and row[mapping['zona']].strip():
                    zona_nombre = row[mapping['zona']].strip()
                    zona = zonas_por_nombre.get(zona_nombre.lower())

                if not zona:
                    zona = next(iter(zonas_por_nombre.values()), None)
                if not zona:
                    errores += 1
                    continue

                tipo = 'casa'
                if 'tipo' in mapping:
                    tipo = validar_tipo(row[mapping['tipo']].strip().lower() or detectar_tipo_inmueble(titulo))

                datos = {
                    'titulo': titulo[:300],
                    'precio_publicado': precio,
                    'zona_id': zona.pk,
                    'tipo_inmueble': tipo,
                    'descripcion': row[mapping['descripcion']].strip() if 'descripcion' in mapping else '',
                    'url_anuncio': row[mapping['url']].strip() if 'url' in mapping else '',
                    'direccion': row[mapping['direccion']].strip() if 'direccion' in mapping else '',
                    'estado_fisico': 'regular',
                }

                if 'm2_terreno' in mapping:
                    datos['m2_terreno'] = parse_metros(row[mapping['m2_terreno']]) or None
                if 'm2_construccion' in mapping:
                    datos['m2_construccion'] = parse_metros(row[mapping['m2_construccion']]) or None

                _, es_nueva = registrar_desde_fuente(datos, fuente, capturado_por=usuario)
                if es_nueva:
                    nuevos += 1
                else:
                    actualizados += 1
            except (IndexError, ValueError):
                errores += 1

        return {'nuevos': nuevos, 'actualizados': actualizados, 'errores': errores}