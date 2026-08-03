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

PRESUPUESTO ACTIVO (Fase 3 del módulo de presupuestos)
------------------------------------------------------
Si la propiedad tiene un ``Presupuesto`` marcado ``es_activo``, su total MANDA
sobre la estimación paramétrica: un presupuesto por partidas tiene precisión de
±5–10% frente al ±25–40% del costo por m².

Este es el ÚNICO punto de integración con el ROI, a propósito: ``estimar()`` es
lo que alimenta la partida de reparaciones en ``OportunidadService``, así que
todo lo de aguas abajo —inversión total, ROI, semáforo, alertas— sigue siendo el
mismo código de siempre. Duplicar la fórmula del ROI aquí habría creado dos
verdades que se desincronizan.
"""

# El servidor corre Python 3.9: sin esto, una anotación como `Decimal | None`
# se evalúa al importar y truena con "unsupported operand type(s) for |".
from __future__ import annotations

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
    def presupuesto_activo(cls, propiedad):
        """Presupuesto marcado ``es_activo`` de la propiedad, o None.

        Import local: ``presupuestos`` depende de ``propiedades``, y hacerlo
        arriba cerraría el ciclo al cargar las apps.
        """
        if not propiedad.pk:
            return None
        from presupuestos.models import Presupuesto

        return (
            Presupuesto.objects
            .filter(propiedad=propiedad, es_activo=True)
            .prefetch_related('partidas')
            .first()
        )

    @classmethod
    def desde_presupuesto(cls, presupuesto, propiedad):
        """Convierte un presupuesto en el mismo dict que devuelve ``estimar()``.

        El ``costo_m2`` se deriva del área DEL PRESUPUESTO, no de la propiedad:
        el usuario pudo presupuestar solo una parte de la construcción, y esa es
        la superficie a la que corresponde el total.

        ``nivel_obra`` sigue siendo el de la propiedad, NO el ``tipo_obra`` del
        presupuesto: alimenta ``AnalisisInversion.nivel_remodelacion_aplicado``,
        que tiene ``choices`` de nivel (ninguna/ligera/media/completa), y meterle
        'remodelacion' dejaría un valor fuera de catálogo que el admin mostraría
        en crudo.

        Se toma ``costo_para_roi`` y NO ``total``: las obras se administran
        directamente, así que la utilidad es margen y no desembolso. Sumarla a la
        inversión castigaría el ROI con dinero que nadie paga.
        """
        total = presupuesto.costo_para_roi
        area = presupuesto.area_m2 or Decimal('0')
        return {
            'nivel_obra': propiedad.nivel_remodelacion_efectivo,
            'tipo_obra': presupuesto.tipo_obra,
            'costo_m2': (total / area).quantize(Decimal('0.01')) if area > 0 else Decimal('0'),
            'm2_base': Decimal(str(area)).quantize(Decimal('0.01')),
            'presupuesto': total,
            'es_estimado': False,   # viene de partidas, no de un costo genérico
            'origen': 'presupuesto',
            'presupuesto_id': presupuesto.pk,
            'presupuesto_nombre': presupuesto.nombre,
        }

    @classmethod
    def estimar(cls, propiedad):
        """
        Devuelve un dict con el desglose del presupuesto de remodelación:
          nivel_obra, costo_m2, m2_base, presupuesto, es_estimado, origen

        Si hay presupuesto activo, MANDA sobre el estimado paramétrico.
        """
        activo = cls.presupuesto_activo(propiedad)
        if activo is not None:
            return cls.desde_presupuesto(activo, propiedad)

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
                'origen': 'parametrico',
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
            'origen': 'parametrico',
        }
