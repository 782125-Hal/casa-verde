"""
Siembra costos de remodelación por m² para cada zona de mercado.

Parte de los costos base globales (core.choices.DEFAULT_COSTO_REMODELACION_M2)
y los escala por zona según su valor de construcción por m² relativo a una
referencia, de modo que zonas más caras tengan costos de obra más altos.

Uso:
    python manage.py seed_remodelacion
    python manage.py seed_remodelacion --sobrescribir   # reescribe existentes
"""
from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand

from core.choices import DEFAULT_COSTO_REMODELACION_M2
from geografia.models import ZonaMercado
from mercado.models import CostoRemodelacionM2, ValorMetroCuadrado

# Valor de construcción por m² de referencia (Tijuana promedio) para escalar.
BASELINE_CONSTRUCCION_M2 = Decimal('15000')
FACTOR_MIN = Decimal('0.70')
FACTOR_MAX = Decimal('1.60')
NIVELES_CON_OBRA = ['ligera', 'media', 'completa']


class Command(BaseCommand):
    help = 'Siembra costos de remodelación por m² por zona y nivel de obra.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sobrescribir', action='store_true',
            help='Reescribe los costos aunque ya existan.',
        )

    def _factor_zona(self, zona):
        """Factor de escala según el valor de construcción m² de la zona."""
        ref = (
            ValorMetroCuadrado.objects
            .filter(zona=zona, valor_construccion_m2__gt=0)
            .order_by('-fecha_actualizacion')
            .first()
        )
        if not ref:
            return Decimal('1.0')
        factor = Decimal(ref.valor_construccion_m2) / BASELINE_CONSTRUCCION_M2
        return max(FACTOR_MIN, min(FACTOR_MAX, factor))

    def handle(self, *args, **options):
        sobrescribir = options['sobrescribir']
        hoy = date.today()
        creados = actualizados = omitidos = 0

        zonas = ZonaMercado.objects.all()
        if not zonas.exists():
            self.stdout.write(self.style.WARNING(
                'No hay zonas de mercado. Ejecuta primero: python manage.py seed_datos'
            ))
            return

        for zona in zonas:
            factor = self._factor_zona(zona)
            for nivel in NIVELES_CON_OBRA:
                base = Decimal(str(DEFAULT_COSTO_REMODELACION_M2[nivel]))
                # Redondeo a la centena más cercana.
                costo = (base * factor / Decimal('100')).quantize(Decimal('1')) * Decimal('100')

                existente = CostoRemodelacionM2.objects.filter(
                    zona=zona, nivel_obra=nivel,
                ).first()

                if existente and not sobrescribir:
                    omitidos += 1
                    continue

                if existente:
                    existente.costo_m2 = costo
                    existente.fecha_actualizacion = hoy
                    existente.notas = f'Sembrado (factor zona {factor:.2f})'
                    existente.save()
                    actualizados += 1
                else:
                    CostoRemodelacionM2.objects.create(
                        zona=zona,
                        nivel_obra=nivel,
                        costo_m2=costo,
                        fecha_actualizacion=hoy,
                        confiabilidad=3,
                        notas=f'Sembrado (factor zona {factor:.2f})',
                    )
                    creados += 1

        self.stdout.write(self.style.SUCCESS(
            f'Costos de remodelación: {creados} creados, '
            f'{actualizados} actualizados, {omitidos} omitidos '
            f'({zonas.count()} zonas × {len(NIVELES_CON_OBRA)} niveles).'
        ))
