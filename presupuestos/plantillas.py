"""Plantillas de presupuesto: precargan las partidas típicas de cada tipo de obra.

El diseño (§3.3) las pide para que al crear un presupuesto solo haya que ajustar
cantidades en vez de armarlo desde cero.

Cada renglón referencia un ``codigo`` del catálogo sembrado por ``seed_catalogo``.
La cantidad se deja en 0: **el sistema no adivina metros cuadrados**. Poner
cantidades inventadas daría un total con apariencia de cálculo que en realidad no
lo es, y ese número acabaría alimentando el ROI en Fase 3.

Si un código no existe en el catálogo (porque nadie corrió ``seed_catalogo`` o se
desactivó), la partida simplemente se omite y la vista lo informa: es preferible
un presupuesto con menos renglones que uno con partidas fantasma.
"""
from presupuestos.choices import TIPO_OBRA_NUEVA, TIPO_OBRA_REMODELACION

# clave -> {nombre, tipo_obra, descripcion, conceptos: [códigos del catálogo]}
PLANTILLAS = {
    'remodelacion_cosmetica': {
        'nombre': 'Remodelación cosmética',
        'tipo_obra': TIPO_OBRA_REMODELACION,
        'descripcion': (
            'Pintura, pisos y detalles. Sin tocar instalaciones ni estructura '
            '(~$600–1,500/m² de costo directo).'
        ),
        'conceptos': [
            'DEM-002',  # retiro de piso existente
            'DEM-003',  # retiro de escombro
            'PIS-001',  # piso cerámico
            'PIS-004',  # zoclo
            'PIN-001',  # pintura interior
            'PIN-003',  # aplanado fino
            'ELA-003',  # luminarias
            'LIM-001',  # limpieza de entrega
        ],
    },
    'remodelacion_integral': {
        'nombre': 'Remodelación integral',
        'tipo_obra': TIPO_OBRA_REMODELACION,
        'descripcion': (
            'Instalaciones nuevas, cocina y baños completos '
            '(~$4,000–8,000/m² de costo directo).'
        ),
        'conceptos': [
            'DEM-001', 'DEM-002', 'DEM-003', 'DEM-004',
            'REP-001', 'REP-002',
            'COC-001', 'COC-002', 'COC-003', 'COC-004',
            'BAN-001', 'BAN-002', 'BAN-003', 'BAN-004',
            'PIS-001', 'PIS-004',
            'ELA-001', 'ELA-002', 'ELA-003',
            'HIA-001', 'HIA-002', 'HIA-003',
            'PIN-001', 'PIN-003',
            'CAR-001', 'CAR-002', 'CAR-003',
            'LIM-001',
        ],
    },
    'obra_nueva_media': {
        'nombre': 'Obra nueva media',
        'tipo_obra': TIPO_OBRA_NUEVA,
        'descripcion': (
            'Vivienda de nivel medio, las 10 partidas del §2.2 '
            '(~$18,000–22,500/m² de costo directo).'
        ),
        'conceptos': [
            'PRE-001', 'PRE-002',
            'CIM-001', 'CIM-002', 'CIM-003',
            'EST-001', 'EST-002', 'EST-003',
            'ALB-001', 'ALB-002',
            'HID-001',
            'ELE-001',
            'ACA-001', 'PIS-001', 'PIN-001', 'PIN-002',
            'CAR-001', 'CAR-002', 'CAR-003',
            'EXT-001', 'EXT-002',
            'LIM-001',
        ],
    },
}

PLANTILLA_CHOICES = [('', 'Sin plantilla — empezar en blanco')] + [
    (clave, f'{datos["nombre"]} — {datos["descripcion"]}')
    for clave, datos in PLANTILLAS.items()
]


def aplicar_plantilla(presupuesto, clave: str) -> tuple[int, list[str]]:
    """Crea las partidas de la plantilla en el presupuesto.

    Devuelve ``(creadas, codigos_faltantes)``. Copia descripción, unidad y PU del
    catálogo al renglón —no los lee por la FK— para que el presupuesto conserve el
    precio con el que se armó aunque el catálogo suba después.
    """
    from presupuestos.models import CatalogoConcepto, PartidaPresupuesto

    plantilla = PLANTILLAS.get(clave)
    if not plantilla:
        return 0, []

    codigos = plantilla['conceptos']
    encontrados = {
        c.codigo: c
        for c in CatalogoConcepto.objects.filter(codigo__in=codigos, activo=True)
    }
    partidas = []
    for orden, codigo in enumerate(codigos, start=1):
        concepto = encontrados.get(codigo)
        if concepto is None:
            continue
        partidas.append(PartidaPresupuesto(
            presupuesto=presupuesto,
            concepto=concepto,
            categoria=concepto.categoria,
            descripcion=concepto.descripcion,
            unidad=concepto.unidad,
            cantidad=0,
            pu=concepto.pu_total,
            orden=orden,
        ))
    PartidaPresupuesto.objects.bulk_create(partidas)
    faltantes = [c for c in codigos if c not in encontrados]
    return len(partidas), faltantes
