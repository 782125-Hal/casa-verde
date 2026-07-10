"""
Servicio de estimación de presupuesto de remodelación — Casa Verde

Método: costo por m² según nivel de obra, con precios por zona.

  presupuesto = m²_construcción × costo_m²(zona, nivel_obra)

El nivel de obra se toma de la propiedad (campo nivel_remodelacion) o, si no
se capturó, se deriva del estado físico mediante
core.choices.ESTADO_FISICO_A_NIVEL_REMODELACION.

El costo por m² se busca primero en la zona (mercado.CostoRemodelacionM2). Si la
zona aún no tiene ese nivel capturado, se usa el fallback global
core.choices.DEFAULT_COSTO_REMODELACION_M2 y se marca el resultado como estimado.
"""
from decimal import Decimal

from core.choices import DEFAULT_COSTO_REMODELACION_M2
from mercado.models import CostoRemodelacionM2


class RemodelacionService:
    """Estima el presupuesto de remodelación de una propiedad."""

    @classmethod
    def costo_m2_fallback(cls, nivel_obra):
        """Costo global por m² para un nivel de obra (fallback)."""
        return Decimal(str(DEFAULT_COSTO_REMODELACION_M2.get(nivel_obra, 0)))

    @classmethod
    def superficie_base(cls, propiedad):
        """
        Superficie sobre la que se calcula la obra: m² de construcción.
        Para terrenos (sin construcción) no hay remodelación → 0.
        """
        if propiedad.m2_construccion and propiedad.m2_construccion > 0:
            return Decimal(str(propiedad.m2_construccion))
        return Decimal('0')

    @classmethod
    def estimar(cls, propiedad):
        """
        Devuelve un dict con el desglose del presupuesto de remodelación:
          nivel_obra, costo_m2, m2_base, presupuesto, es_estimado
        """
        nivel = propiedad.nivel_remodelacion_efectivo
        m2 = cls.superficie_base(propiedad)

        # Nivel "ninguna" o sin superficie → sin presupuesto.
        if nivel == 'ninguna' or m2 <= 0:
            return {
                'nivel_obra': nivel,
                'costo_m2': Decimal('0'),
                'm2_base': m2.quantize(Decimal('0.01')),
                'presupuesto': Decimal('0'),
                'es_estimado': False,
            }

        costo_zona = CostoRemodelacionM2.obtener_costo_m2(propiedad.zona, nivel)
        if costo_zona is not None:
            costo_m2 = Decimal(str(costo_zona))
            es_estimado = False
        else:
            costo_m2 = cls.costo_m2_fallback(nivel)
            es_estimado = True

        presupuesto = (m2 * costo_m2).quantize(Decimal('0.01'))

        return {
            'nivel_obra': nivel,
            'costo_m2': costo_m2.quantize(Decimal('0.01')),
            'm2_base': m2.quantize(Decimal('0.01')),
            'presupuesto': presupuesto,
            'es_estimado': es_estimado,
        }
