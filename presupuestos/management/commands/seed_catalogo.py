"""
Siembra el catálogo base de conceptos (precios unitarios) del módulo de
presupuestos.

Reutiliza los datos de `mercado/management/commands/seed_remodelacion.py`:

- Los conceptos **paramétricos** (uno por nivel de obra) salen directamente de
  `core.choices.DEFAULT_COSTO_REMODELACION_M2`, la MISMA fuente que usa
  seed_remodelacion. Así el estimado rápido del §2.1 y el costo que ya maneja
  el análisis de inversión no pueden divergir.
- Con `--zona <id|nombre>` se usan en su lugar los `CostoRemodelacionM2` que
  seed_remodelacion ya calculó para esa zona, que están escalados por el valor
  de construcción local.

Los conceptos **detallados** traen PU orientativos de los rangos del §2.5
(Tijuana 2026). NO son cotizaciones: el diseño es explícito en que hay que pedir
3 cotizaciones por partida grande y construir el catálogo con precios que uno
mismo pagó. Sirven para arrancar y para que el presupuesto detallado no empiece
en blanco.

Uso:
    python manage.py seed_catalogo
    python manage.py seed_catalogo --sobrescribir       # reescribe los existentes
    python manage.py seed_catalogo --zona 3             # PU paramétricos de esa zona
"""

# El servidor corre Python 3.9: sin esto, una anotación como `Decimal | None`
# se evalúa al importar y truena con "unsupported operand type(s) for |".
from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand

from core.choices import DEFAULT_COSTO_REMODELACION_M2
from mercado.models import CostoRemodelacionM2
from presupuestos.choices import NIVEL_PARAMETRICO_A_CODIGO
from presupuestos.models import CatalogoConcepto

# (codigo, descripcion, categoria, unidad, pu_material, pu_mano_obra, pu_equipo)
# PU en MXN, orientativos (§2.5). Reemplazar con cotizaciones propias.
CONCEPTOS_BASE = [
    # --- Remodelación: demolición y retiro -------------------------------------
    ('DEM-001', 'Demolición de muro de tabique, incluye acarreo', 'demolicion', 'm2', 0, 180, 40),
    ('DEM-002', 'Retiro de piso existente (loseta o cerámica)', 'demolicion', 'm2', 0, 120, 25),
    ('DEM-003', 'Retiro de escombro a tiro autorizado', 'demolicion', 'm3', 0, 250, 350),
    ('DEM-004', 'Desmontaje de muebles de baño y cocina', 'demolicion', 'lote', 0, 2500, 0),
    # --- Reparaciones estructurales / humedades --------------------------------
    ('REP-001', 'Resane e impermeabilización de muro con humedad', 'reparaciones', 'm2', 180, 220, 20),
    ('REP-002', 'Impermeabilización de losa, sistema prefabricado 5 años', 'reparaciones', 'm2', 190, 130, 30),
    ('REP-003', 'Refuerzo de castillo o trabe existente', 'reparaciones', 'ml', 850, 900, 150),
    # --- Cocina -----------------------------------------------------------------
    ('COC-001', 'Mueble de cocina inferior, melamina, incluye herrajes', 'cocina', 'ml', 3800, 1200, 0),
    ('COC-002', 'Mueble de cocina superior, melamina', 'cocina', 'ml', 2900, 950, 0),
    ('COC-003', 'Cubierta de granito o cuarzo, incluye zoclo', 'cocina', 'ml', 4200, 1100, 200),
    ('COC-004', 'Tarja doble de acero inoxidable con monomando', 'cocina', 'pza', 3500, 850, 0),
    # --- Baños -------------------------------------------------------------------
    ('BAN-001', 'Mueble de baño: WC, lavabo y accesorios (gama media)', 'banos', 'jgo', 7500, 2200, 0),
    ('BAN-002', 'Azulejo en muro de baño, incluye boquilla', 'banos', 'm2', 320, 380, 30),
    ('BAN-003', 'Cancel de cristal templado 6 mm para regadera', 'banos', 'pza', 6800, 1500, 0),
    ('BAN-004', 'Mezcladora para regadera, gama media', 'banos', 'pza', 1800, 550, 0),
    # --- Pisos y recubrimientos --------------------------------------------------
    ('PIS-001', 'Piso cerámico 60x60, incluye pegazulejo y boquilla', 'pisos', 'm2', 280, 260, 30),
    ('PIS-002', 'Piso porcelánico gran formato', 'pisos', 'm2', 520, 340, 40),
    ('PIS-003', 'Piso laminado con base aislante', 'pisos', 'm2', 340, 190, 20),
    ('PIS-004', 'Zoclo de madera o MDF, 7 cm', 'pisos', 'ml', 95, 65, 0),
    # --- Instalación eléctrica (actualización) -----------------------------------
    ('ELA-001', 'Salida eléctrica nueva (contacto o apagador)', 'electrica_act', 'salida', 320, 480, 40),
    ('ELA-002', 'Cambio de centro de carga 8 circuitos con pastillas', 'electrica_act', 'pza', 3800, 1900, 100),
    ('ELA-003', 'Luminaria empotrada LED, incluye instalación', 'electrica_act', 'pza', 380, 220, 0),
    # --- Instalación hidrosanitaria (actualización) ------------------------------
    ('HIA-001', 'Cambio de tubería hidráulica CPVC por salida', 'hidro_act', 'salida', 450, 620, 60),
    ('HIA-002', 'Cambio de tubería sanitaria PVC 4"', 'hidro_act', 'ml', 280, 340, 40),
    ('HIA-003', 'Calentador de paso instalado', 'hidro_act', 'pza', 6500, 1200, 0),
    # --- Pintura y acabados -------------------------------------------------------
    ('PIN-001', 'Pintura vinílica en muro interior, 2 manos', 'pintura', 'm2', 35, 50, 0),
    ('PIN-002', 'Pintura en fachada, incluye sellador', 'pintura', 'm2', 48, 72, 15),
    ('PIN-003', 'Aplanado fino de yeso en muro', 'pintura', 'm2', 60, 140, 10),
    # --- Carpintería y cancelería (ambos tipos de obra) ---------------------------
    ('CAR-001', 'Puerta interior de madera con marco y herrajes', 'carpinteria', 'pza', 3200, 950, 0),
    ('CAR-002', 'Clóset de melamina con entrepaños y tubo', 'carpinteria', 'ml', 4100, 1300, 0),
    ('CAR-003', 'Ventana de aluminio con cristal 6 mm', 'carpinteria', 'm2', 2200, 650, 50),
    # --- Limpieza y entrega (ambos) ------------------------------------------------
    ('LIM-001', 'Limpieza fina de entrega', 'limpieza', 'm2', 15, 45, 5),
    # --- Obra nueva: preliminares ---------------------------------------------------
    ('PRE-001', 'Limpieza y despalme de terreno', 'preliminares', 'm2', 0, 55, 45),
    ('PRE-002', 'Trazo y nivelación con equipo topográfico', 'preliminares', 'm2', 12, 38, 30),
    # --- Cimentación -------------------------------------------------------------------
    ('CIM-001', 'Excavación en material tipo B, medios mecánicos', 'cimentacion', 'm3', 0, 180, 320),
    ('CIM-002', 'Zapata corrida de concreto f\'c=200, armada', 'cimentacion', 'm3', 3200, 1800, 400),
    ('CIM-003', 'Firme de concreto 10 cm armado con malla', 'cimentacion', 'm2', 320, 210, 60),
    # --- Estructura ----------------------------------------------------------------------
    ('EST-001', 'Castillo armado de concreto 15x20 cm', 'estructura', 'ml', 380, 320, 50),
    ('EST-002', 'Losa de vigueta y bovedilla, 15 cm', 'estructura', 'm2', 780, 520, 120),
    ('EST-003', 'Trabe de concreto armado 20x30 cm', 'estructura', 'ml', 920, 680, 110),
    # --- Albañilería ---------------------------------------------------------------------
    ('ALB-001', 'Muro de block hueco 15x20x40, asentado', 'albanileria', 'm2', 340, 290, 30),
    ('ALB-002', 'Aplanado de mezcla en muro, acabado fino', 'albanileria', 'm2', 85, 165, 15),
    # --- Instalaciones de obra nueva -------------------------------------------------------
    ('HID-001', 'Instalación hidrosanitaria completa por salida', 'hidrosanitaria', 'salida', 620, 780, 70),
    ('ELE-001', 'Instalación eléctrica completa por salida', 'electrica', 'salida', 380, 560, 50),
    # --- Acabados de obra nueva --------------------------------------------------------------
    ('ACA-001', 'Suministro y colocación de loseta cerámica', 'acabados', 'm2', 290, 270, 30),
    # --- Exteriores -----------------------------------------------------------------------------
    ('EXT-001', 'Barda de block de 2.20 m, incluye castillos', 'exteriores', 'ml', 1250, 980, 120),
    ('EXT-002', 'Piso de concreto estampado en cochera', 'exteriores', 'm2', 420, 380, 90),
]


class Command(BaseCommand):
    help = 'Siembra el catálogo base de conceptos con precios unitarios.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sobrescribir', action='store_true',
            help='Reescribe los conceptos aunque ya existan.',
        )
        parser.add_argument(
            '--zona', default=None,
            help='ID o nombre de zona: toma los PU paramétricos de sus '
                 'CostoRemodelacionM2 (ya escalados por seed_remodelacion) en vez '
                 'de los costos globales por defecto.',
        )

    def _costos_parametricos(self, zona_arg):
        """{nivel: costo_m2}. De la zona si se pidió; si no, los globales.

        Es la MISMA fuente que usa seed_remodelacion, para que el estimado rápido
        y el análisis de inversión no puedan divergir.
        """
        globales = {
            nivel: Decimal(str(costo))
            for nivel, costo in DEFAULT_COSTO_REMODELACION_M2.items()
            if nivel in NIVEL_PARAMETRICO_A_CODIGO
        }
        if not zona_arg:
            return globales, 'costos globales por defecto'

        filtro = {'zona_id': zona_arg} if str(zona_arg).isdigit() else {'zona__nombre__icontains': zona_arg}
        por_zona = CostoRemodelacionM2.objects.filter(**filtro, costo_m2__gt=0)
        if not por_zona.exists():
            self.stdout.write(self.style.WARNING(
                f'No hay CostoRemodelacionM2 para la zona {zona_arg!r}. '
                'Ejecuta antes: python manage.py seed_remodelacion. '
                'Se usan los costos globales.'
            ))
            return globales, 'costos globales por defecto (zona sin datos)'

        costos = dict(globales)
        for registro in por_zona:
            if registro.nivel_obra in NIVEL_PARAMETRICO_A_CODIGO:
                costos[registro.nivel_obra] = Decimal(registro.costo_m2)
        etiqueta = f'CostoRemodelacionM2 de la zona {por_zona.first().zona}'
        return costos, etiqueta

    def _conceptos_parametricos(self, costos):
        """Un concepto por nivel de obra: el estimado rápido del §2.1.

        Todo el costo va a mano de obra=0/material=0 y se concentra en un PU
        único: es un precio alzado por m², no un desglose.
        """
        for nivel, codigo in NIVEL_PARAMETRICO_A_CODIGO.items():
            costo = costos.get(nivel)
            if not costo:
                continue
            yield (
                codigo,
                f'Estimado paramétrico — remodelación {nivel} (precio alzado por m²)',
                'preliminares', 'm2', costo, Decimal('0'), Decimal('0'),
            )

    def handle(self, *args, **options):
        sobrescribir = options['sobrescribir']
        costos, origen = self._costos_parametricos(options['zona'])
        hoy = date.today()
        creados = actualizados = omitidos = 0

        filas = list(self._conceptos_parametricos(costos)) + [
            (c, d, cat, u, Decimal(str(m)), Decimal(str(mo)), Decimal(str(e)))
            for c, d, cat, u, m, mo, e in CONCEPTOS_BASE
        ]

        for codigo, descripcion, categoria, unidad, material, mano_obra, equipo in filas:
            valores = {
                'descripcion': descripcion,
                'categoria': categoria,
                'unidad': unidad,
                'pu_material': material,
                'pu_mano_obra': mano_obra,
                'pu_equipo': equipo,
                'vigencia': hoy,
                'activo': True,
            }
            existente = CatalogoConcepto.objects.filter(codigo=codigo).first()
            if existente is None:
                CatalogoConcepto.objects.create(codigo=codigo, **valores)
                creados += 1
            elif sobrescribir:
                for campo, valor in valores.items():
                    setattr(existente, campo, valor)
                existente.save()
                actualizados += 1
            else:
                omitidos += 1

        self.stdout.write(f'PU paramétricos tomados de: {origen}')
        self.stdout.write(self.style.SUCCESS(
            f'Catálogo sembrado: {creados} creados, {actualizados} actualizados, '
            f'{omitidos} omitidos (ya existían).'
        ))
        if omitidos and not sobrescribir:
            self.stdout.write(
                'Usa --sobrescribir para reescribir los que ya estaban.'
            )
        self.stdout.write(self.style.WARNING(
            'Los PU detallados son ORIENTATIVOS (§2.5). Sustitúyelos por tus '
            'cotizaciones: la regla del diseño es 3 cotizaciones por partida grande.'
        ))
