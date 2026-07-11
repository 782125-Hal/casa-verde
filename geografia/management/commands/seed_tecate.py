"""
Agrega Tecate, B.C. como ciudad con zonas y valores de mercado de EJEMPLO.

Los valores por m² son estimaciones iniciales (Tecate es un mercado más pequeño
y económico que Tijuana) — ajústalos con datos reales en el admin.

Uso:
    python manage.py seed_tecate

Después ejecuta `python manage.py seed_remodelacion` para generar los costos de
remodelación de las nuevas zonas.
"""
from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand

from geografia.models import Estado, Municipio, ZonaMercado
from mercado.models import FuenteDatos, ValorMetroCuadrado

# Zonas de Tecate con valores por m² de EJEMPLO (MXN). Calibrar en el admin.
ZONAS_TECATE = [
    {
        'nombre': 'Tecate Centro',
        'colonia': 'Centro',
        'ciudad': 'Tecate',
        'radio_metros': 2000,
        'valores': {
            'casa': {'terreno': 4500, 'construccion': 11000, 'min': 900000, 'prom': 1600000, 'max': 2600000},
            'departamento': {'terreno': 0, 'construccion': 12000, 'min': 700000, 'prom': 1200000, 'max': 1900000},
            'terreno': {'terreno': 3800, 'construccion': 0, 'min': 500000, 'prom': 900000, 'max': 1500000},
            'local': {'terreno': 5200, 'construccion': 11500, 'min': 1000000, 'prom': 1800000, 'max': 3000000},
        },
    },
    {
        'nombre': 'Hidalgo',
        'colonia': 'Hidalgo',
        'ciudad': 'Tecate',
        'radio_metros': 2500,
        'valores': {
            'casa': {'terreno': 3800, 'construccion': 10000, 'min': 800000, 'prom': 1350000, 'max': 2100000},
            'departamento': {'terreno': 0, 'construccion': 11000, 'min': 650000, 'prom': 1050000, 'max': 1600000},
            'terreno': {'terreno': 3200, 'construccion': 0, 'min': 420000, 'prom': 780000, 'max': 1250000},
            'local': {'terreno': 4400, 'construccion': 10500, 'min': 900000, 'prom': 1550000, 'max': 2500000},
        },
    },
    {
        'nombre': 'Encinos',
        'colonia': 'Los Encinos',
        'ciudad': 'Tecate',
        'radio_metros': 3000,
        'valores': {
            'casa': {'terreno': 3200, 'construccion': 9000, 'min': 700000, 'prom': 1150000, 'max': 1800000},
            'departamento': {'terreno': 0, 'construccion': 10000, 'min': 600000, 'prom': 950000, 'max': 1450000},
            'terreno': {'terreno': 2600, 'construccion': 0, 'min': 350000, 'prom': 640000, 'max': 1050000},
            'local': {'terreno': 3800, 'construccion': 9500, 'min': 800000, 'prom': 1350000, 'max': 2200000},
        },
    },
    {
        'nombre': 'Valle de las Palmas',
        'colonia': 'Valle de las Palmas',
        'ciudad': 'Tecate',
        'radio_metros': 4000,
        'valores': {
            'casa': {'terreno': 2400, 'construccion': 8000, 'min': 550000, 'prom': 950000, 'max': 1500000},
            'terreno': {'terreno': 1900, 'construccion': 0, 'min': 280000, 'prom': 520000, 'max': 900000},
            'local': {'terreno': 3000, 'construccion': 8500, 'min': 650000, 'prom': 1150000, 'max': 1900000},
        },
    },
]


class Command(BaseCommand):
    help = 'Agrega Tecate, B.C. con zonas y valores de mercado de ejemplo.'

    def handle(self, *args, **options):
        bc = Estado.objects.get_or_create(
            clave='BC', defaults={'nombre': 'Baja California'},
        )[0]
        tecate = Municipio.objects.get_or_create(estado=bc, nombre='Tecate')[0]

        fuente_manual = FuenteDatos.objects.get_or_create(
            nombre='Captura manual',
            defaults={'tipo': 'manual', 'activa': True},
        )[0]

        zonas_ok = 0
        valores_ok = 0
        for zdata in ZONAS_TECATE:
            zona, _ = ZonaMercado.objects.update_or_create(
                municipio=tecate,
                nombre=zdata['nombre'],
                defaults={
                    'colonia': zdata['colonia'],
                    'ciudad': zdata['ciudad'],
                    'radio_metros': zdata['radio_metros'],
                    'activa': True,
                },
            )
            zonas_ok += 1
            for tipo, vals in zdata['valores'].items():
                ValorMetroCuadrado.objects.update_or_create(
                    zona=zona,
                    tipo_inmueble=tipo,
                    fecha_actualizacion=date.today(),
                    defaults={
                        'valor_terreno_m2': Decimal(str(vals['terreno'])),
                        'valor_construccion_m2': Decimal(str(vals['construccion'])),
                        'valor_min': Decimal(str(vals['min'])) if vals.get('min') else None,
                        'valor_promedio': Decimal(str(vals['prom'])) if vals.get('prom') else None,
                        'valor_max': Decimal(str(vals['max'])) if vals.get('max') else None,
                        'confiabilidad': 2,
                        'fuente': fuente_manual,
                        'servicios': 'Agua, luz, drenaje',
                        'notas': 'Valor de EJEMPLO — calibrar con datos reales.',
                    },
                )
                valores_ok += 1

        self.stdout.write(self.style.SUCCESS(
            f'Tecate configurado: {zonas_ok} zonas, {valores_ok} valores por m² (de ejemplo).'
        ))
        self.stdout.write(
            'Ahora ejecuta: python manage.py seed_remodelacion  '
            '(para los costos de remodelación de Tecate).'
        )
