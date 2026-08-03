"""
Servicio de valoración inmobiliaria — Casa Verde

Fórmulas:
  Valor terreno     = m²_terreno × valor_m²_terreno_zona
  Valor construcción = m²_construidos × valor_m²_construcción × factor_estado_físico
  Valor total       = valor_terreno + valor_construcción

OBRA NUEVA (comprar terreno + construir)
----------------------------------------
Un terreno todavía no tiene m² construidos, así que la valuación normal daría
solo el valor del suelo y el ROI de un proyecto de construcción saldría siempre
en rojo. Si la propiedad es un terreno con un ``Presupuesto`` de obra nueva
marcado ``es_activo``, su ``area_m2`` es lo que se edificará y el resultado se
valúa como CASA TERMINADA (suelo + construcción al valor de casa de la zona):
eso es lo que se vendería. Con esto, la MISMA cadena de siempre —inversión, ROI,
semáforo— responde "¿es negocio construir aquí?" sin lógica financiera nueva.
"""
from decimal import Decimal

from core.choices import FACTOR_ESTADO_FISICO
from mercado.models import ValorMetroCuadrado


class ValoracionService:
    """Calcula el valor estimado de mercado de una propiedad."""

    FACTOR_ANTIGUEDAD_POR_DECADA = Decimal('0.02')  # -2% por década
    FACTOR_MIN_ANTIGUEDAD = Decimal('0.70')

    # La obra nueva se valúa como casa terminada: es el producto que se vende.
    TIPO_INMUEBLE_OBRA_NUEVA = 'casa'

    @classmethod
    def obtener_valor_referencia_tipo(cls, zona, tipo_inmueble):
        """ValorMetroCuadrado más reciente para una zona y un tipo dados."""
        return ValorMetroCuadrado.objects.filter(
            zona=zona,
            tipo_inmueble=tipo_inmueble,
        ).order_by('-fecha_actualizacion').first()

    @classmethod
    def obtener_valor_referencia(cls, propiedad):
        """Obtiene el ValorMetroCuadrado más reciente para la zona y tipo."""
        return cls.obtener_valor_referencia_tipo(propiedad.zona, propiedad.tipo_inmueble)

    @classmethod
    def obra_nueva_activa(cls, propiedad):
        """(area_a_construir, referencia_casa) si la propiedad es un terreno con
        un presupuesto de obra nueva activo; si no, None.

        - Solo aplica cuando la propiedad NO tiene m² construidos (si ya los
          tiene, se valúa como cualquier inmueble).
        - La referencia es la de CASA de la zona: el terreno se convierte en
          casa terminada, y esa es la tabla de valor de venta correspondiente.

        Import local: ``presupuestos`` depende de ``propiedades``; importar
        arriba cerraría el ciclo al cargar las apps (mismo motivo que en
        RemodelacionService).
        """
        if propiedad.m2_construccion and propiedad.m2_construccion > 0:
            return None
        if not propiedad.pk:
            return None
        from presupuestos.choices import TIPO_OBRA_NUEVA
        from presupuestos.models import Presupuesto

        activo = (
            Presupuesto.objects
            .filter(propiedad=propiedad, es_activo=True, tipo_obra=TIPO_OBRA_NUEVA)
            .first()
        )
        if activo is None or not activo.area_m2 or activo.area_m2 <= 0:
            return None
        referencia = cls.obtener_valor_referencia_tipo(
            propiedad.zona, cls.TIPO_INMUEBLE_OBRA_NUEVA,
        )
        if referencia is None:
            return None
        return Decimal(str(activo.area_m2)), referencia

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

        obra_nueva = cls.obra_nueva_activa(propiedad)
        construccion_proyectada = obra_nueva is not None

        if construccion_proyectada:
            # Casa terminada = suelo + construcción a valor de casa de la zona.
            # La construcción es NUEVA, así que no se aplica factor de estado
            # físico (equivale a 'excelente' = 1.0); la referencia pasa a ser la
            # de casa para que 'datos_completos' y el suelo usen esa tabla.
            area_a_construir, referencia = obra_nueva
            valor_terreno = (propiedad.m2_terreno or Decimal('0')) * referencia.valor_terreno_m2
            valor_construccion = area_a_construir * referencia.valor_construccion_m2
            superficie = {'estimado': False}
        else:
            valor_terreno = cls.calcular_valor_terreno(propiedad, referencia)
            valor_construccion = cls.calcular_valor_construccion(propiedad, referencia, factor_estado)
            superficie = cls.estimar_superficie_faltante(propiedad, referencia)

        valor_total = (valor_terreno + valor_construccion) * factor_antiguedad * factor_riesgo * factor_ubicacion

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
            'construccion_proyectada': construccion_proyectada,
            'datos_completos': propiedad.tiene_datos_minimos and referencia is not None,
        }