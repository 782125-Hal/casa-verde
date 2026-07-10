"""
Servicio de valoración inmobiliaria — Casa Verde

Fórmulas:
  Valor terreno     = m²_terreno × valor_m²_terreno_zona
  Valor construcción = m²_construidos × valor_m²_construcción × factor_estado_físico
  Valor total       = valor_terreno + valor_construcción
"""
from decimal import Decimal

from core.choices import FACTOR_ESTADO_FISICO
from mercado.models import ValorMetroCuadrado


class ValoracionService:
    """Calcula el valor estimado de mercado de una propiedad."""

    FACTOR_ANTIGUEDAD_POR_DECADA = Decimal('0.02')  # -2% por década
    FACTOR_MIN_ANTIGUEDAD = Decimal('0.70')

    @classmethod
    def obtener_valor_referencia(cls, propiedad):
        """Obtiene el ValorMetroCuadrado más reciente para la zona y tipo."""
        return ValorMetroCuadrado.objects.filter(
            zona=propiedad.zona,
            tipo_inmueble=propiedad.tipo_inmueble,
        ).order_by('-fecha_actualizacion').first()

    @classmethod
    def factor_estado_fisico(cls, estado_fisico):
        return Decimal(str(FACTOR_ESTADO_FISICO.get(estado_fisico, 0.75)))

    @classmethod
    def factor_antiguedad(cls, anos):
        if not anos or anos <= 0:
            return Decimal('1.0')
        decadas = Decimal(str(anos)) / Decimal('10')
        factor = Decimal('1.0') - (decadas * cls.FACTOR_ANTIGUEDAD_POR_DECADA)
        return max(factor, cls.FACTOR_MIN_ANTIGUEDAD)

    @classmethod
    def factor_riesgo(cls, propiedad):
        """Penaliza según riesgo documental, legal y físico (RN-04)."""
        riesgo = propiedad.riesgo_total
        penalizaciones = {
            1: Decimal('1.00'),
            2: Decimal('0.95'),
            3: Decimal('0.85'),
            4: Decimal('0.70'),
            5: Decimal('0.50'),
        }
        return penalizaciones.get(riesgo, Decimal('0.85'))

    @classmethod
    def calcular_valor_terreno(cls, propiedad, referencia):
        if not propiedad.m2_terreno or not referencia:
            return Decimal('0')
        return propiedad.m2_terreno * referencia.valor_terreno_m2

    @classmethod
    def calcular_valor_construccion(cls, propiedad, referencia, factor_estado):
        if not propiedad.m2_construccion or not referencia:
            return Decimal('0')
        base = propiedad.m2_construccion * referencia.valor_construccion_m2
        return base * factor_estado

    @classmethod
    def estimar_superficie_faltante(cls, propiedad, referencia):
        """
        Estimación conservadora cuando faltan m² (RN-03).
        Usa precio publicado dividido por valor m² de referencia × 0.85.
        """
        factor_conservador = Decimal('0.85')
        if not propiedad.m2_terreno and not propiedad.m2_construccion and referencia:
            if propiedad.tipo_inmueble == 'terreno' and referencia.valor_terreno_m2 > 0:
                estimado = (propiedad.precio_publicado / referencia.valor_terreno_m2) * factor_conservador
                return {'m2_terreno': estimado, 'm2_construccion': None, 'estimado': True}
            if referencia.valor_construccion_m2 > 0:
                estimado = (propiedad.precio_publicado / referencia.valor_construccion_m2) * factor_conservador
                return {'m2_terreno': None, 'm2_construccion': estimado, 'estimado': True}
        return {'m2_terreno': propiedad.m2_terreno, 'm2_construccion': propiedad.m2_construccion, 'estimado': False}

    @classmethod
    def valorar(cls, propiedad):
        """
        Retorna dict con desglose completo de valoración.
        """
        referencia = cls.obtener_valor_referencia(propiedad)
        factor_estado = cls.factor_estado_fisico(propiedad.estado_fisico)
        factor_antiguedad = cls.factor_antiguedad(propiedad.antiguedad_anos)
        factor_riesgo = cls.factor_riesgo(propiedad)
        factor_ubicacion = Decimal('1.0')

        valor_terreno = cls.calcular_valor_terreno(propiedad, referencia)
        valor_construccion = cls.calcular_valor_construccion(propiedad, referencia, factor_estado)

        valor_total = (valor_terreno + valor_construccion) * factor_antiguedad * factor_riesgo * factor_ubicacion

        superficie = cls.estimar_superficie_faltante(propiedad, referencia)

        return {
            'referencia': referencia,
            'valor_terreno_estimado': valor_terreno.quantize(Decimal('0.01')),
            'valor_construccion_estimado': valor_construccion.quantize(Decimal('0.01')),
            'valor_total_estimado': valor_total.quantize(Decimal('0.01')),
            'factor_estado_fisico': factor_estado,
            'factor_antiguedad': factor_antiguedad,
            'factor_ubicacion': factor_ubicacion,
            'factor_riesgo': factor_riesgo,
            'superficie_estimada': superficie['estimado'],
            'datos_completos': propiedad.tiene_datos_minimos and referencia is not None,
        }