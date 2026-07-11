"""
Servicio de detección de oportunidades — Casa Verde

Fórmulas financieras:
  Inversión total    = precio + notariales + impuestos + comisiones + reparaciones + otros
  Utilidad potencial = valor_estimado - inversión_total
  Descuento mercado   = (valor_estimado - precio_publicado) / valor_estimado × 100
  ROI                = utilidad_potencial / inversión_total × 100
  ROI anualizado     = ROI / años_recuperación
  Años recuperación  = inversión_total / utilidad_potencial_anual_estimada
"""
from decimal import Decimal

from analisis.models import AnalisisInversion
from core.choices import DEFAULT_DESCUENTO_MINIMO, DEFAULT_PLAZO_RECUPERACION, DEFAULT_TASA_BANCARIA
from mercado.models import TasaReferenciaBancaria
from services.remodelacion import RemodelacionService
from services.valoracion import ValoracionService


class OportunidadService:
    """Evalúa si una propiedad representa oportunidad de inversión."""

    # Porcentajes estimados de costos adicionales sobre precio de compra
    PCT_NOTARIALES = Decimal('0.06')
    PCT_IMPUESTOS = Decimal('0.02')
    PCT_COMISIONES = Decimal('0.03')

    @classmethod
    def calcular_costos_adicionales(cls, precio, remodelacion):
        """
        Estima gastos notariales, impuestos, comisiones y remodelación.

        `remodelacion` es el dict devuelto por RemodelacionService.estimar();
        su presupuesto se usa como partida de reparaciones.
        """
        gastos_notariales = precio * cls.PCT_NOTARIALES
        impuestos = precio * cls.PCT_IMPUESTOS
        comisiones = precio * cls.PCT_COMISIONES
        reparaciones = remodelacion['presupuesto']

        return {
            'gastos_notariales': gastos_notariales.quantize(Decimal('0.01')),
            'impuestos': impuestos.quantize(Decimal('0.01')),
            'comisiones': comisiones.quantize(Decimal('0.01')),
            'reparaciones': reparaciones.quantize(Decimal('0.01')),
            'otros_gastos': Decimal('0'),
        }

    @classmethod
    def calcular_metricas_financieras(cls, precio, valor_estimado, costos):
        inversion_total = precio + sum(costos.values())

        utilidad = valor_estimado - inversion_total

        if valor_estimado > 0:
            descuento = ((valor_estimado - precio) / valor_estimado) * Decimal('100')
        else:
            descuento = Decimal('0')

        if inversion_total > 0:
            roi = (utilidad / inversion_total) * Decimal('100')
        else:
            roi = Decimal('0')

        # Años de recuperación: asumiendo utilidad se materializa linealmente
        if utilidad > 0:
            anos = inversion_total / utilidad
            roi_anualizado = roi / anos if anos > 0 else Decimal('0')
        else:
            anos = Decimal('99')
            roi_anualizado = Decimal('0')

        return {
            'inversion_total': inversion_total.quantize(Decimal('0.01')),
            'utilidad_potencial': utilidad.quantize(Decimal('0.01')),
            'descuento_mercado': descuento.quantize(Decimal('0.01')),
            'roi': roi.quantize(Decimal('0.01')),
            'roi_anualizado': roi_anualizado.quantize(Decimal('0.01')),
            'anos_recuperacion': anos.quantize(Decimal('0.01')),
        }

    @classmethod
    def determinar_semaforo(cls, metricas, config):
        """
        Clasifica en verde/amarillo/rojo/gris según reglas de negocio.
        config: dict con descuento_minimo, plazo_max, tasa_bancaria, riesgo_maximo
        """
        if not metricas.get('datos_completos'):
            return 'gris', False, False

        descuento = metricas['descuento_mercado']
        roi_anual = metricas['roi_anualizado']
        anos = metricas['anos_recuperacion']
        # Coercer a Decimal: la config puede venir con floats (p. ej. valores por
        # defecto de un Usuario recién creado), y mezclar float × Decimal falla.
        tasa = Decimal(str(config['tasa_bancaria']))
        desc_min = Decimal(str(config['descuento_minimo']))
        plazo_max = config['plazo_recuperacion_max']
        riesgo = metricas.get('riesgo_total', 1)

        if descuento < 0:
            return 'rojo', False, False

        es_oportunidad = descuento >= desc_min and metricas['utilidad_potencial'] > 0

        es_prioritaria = (
            es_oportunidad
            and anos <= plazo_max
            and roi_anual >= tasa
            and riesgo <= config['riesgo_maximo']
        )

        if es_prioritaria:
            return 'verde', True, True

        if es_oportunidad and (anos <= plazo_max or roi_anual >= tasa):
            return 'amarillo', True, False

        if descuento >= desc_min * Decimal('0.5'):
            return 'amarillo', False, False

        return 'rojo', False, False

    @classmethod
    def generar_recomendacion(cls, semaforo, metricas, es_prioritaria):
        recomendaciones = {
            'verde': (
                f'OPORTUNIDAD PRIORITARIA: Descuento del {metricas["descuento_mercado"]:.1f}% '
                f'vs mercado. ROI anualizado {metricas["roi_anualizado"]:.1f}%. '
                f'Recuperación estimada en {metricas["anos_recuperacion"]:.1f} años. '
                'Se recomienda contactar al vendedor y realizar visita.'
            ),
            'amarillo': (
                f'Oportunidad moderada: Descuento {metricas["descuento_mercado"]:.1f}%. '
                'Requiere análisis adicional, negociación de precio o verificación documental.'
            ),
            'rojo': (
                f'No recomendable: Precio {("por encima" if metricas["descuento_mercado"] < 0 else "sin descuento suficiente")} '
                f'del mercado ({metricas["descuento_mercado"]:.1f}%). ROI {metricas["roi"]:.1f}%.'
            ),
            'gris': 'Datos insuficientes para análisis. Completar m², ubicación o precio.',
        }
        return recomendaciones.get(semaforo, '')

    @classmethod
    def analizar_propiedad(cls, propiedad, usuario=None):
        """
        Ejecuta análisis completo y persiste AnalisisInversion.
        """
        valoracion = ValoracionService.valorar(propiedad)
        remodelacion = RemodelacionService.estimar(propiedad)
        costos = cls.calcular_costos_adicionales(propiedad.precio_publicado, remodelacion)

        metricas = cls.calcular_metricas_financieras(
            propiedad.precio_publicado,
            valoracion['valor_total_estimado'],
            costos,
        )
        metricas['datos_completos'] = valoracion['datos_completos']
        metricas['riesgo_total'] = propiedad.riesgo_total

        if usuario:
            config = {
                'descuento_minimo': usuario.descuento_minimo,
                'plazo_recuperacion_max': usuario.plazo_recuperacion_max,
                'tasa_bancaria': usuario.tasa_ahorro_personal,
                'riesgo_maximo': usuario.riesgo_maximo,
            }
        else:
            config = {
                'descuento_minimo': Decimal(str(DEFAULT_DESCUENTO_MINIMO)),
                'plazo_recuperacion_max': DEFAULT_PLAZO_RECUPERACION,
                'tasa_bancaria': TasaReferenciaBancaria.obtener_tasa_vigente(),
                'riesgo_maximo': 3,
            }

        semaforo, es_oportunidad, es_prioritaria = cls.determinar_semaforo(metricas, config)
        recomendacion = cls.generar_recomendacion(semaforo, metricas, es_prioritaria)

        riesgos = []
        if propiedad.riesgo_documental >= 4:
            riesgos.append('Alto riesgo documental')
        if propiedad.riesgo_legal >= 4:
            riesgos.append('Alto riesgo legal')
        if propiedad.riesgo_fisico >= 4:
            riesgos.append('Alto riesgo físico/estructural')
        if valoracion['superficie_estimada']:
            riesgos.append('Superficie estimada de forma conservadora')
        if remodelacion['es_estimado'] and remodelacion['presupuesto'] > 0:
            riesgos.append('Presupuesto de remodelación con costo genérico (zona sin costo capturado)')

        analisis, _ = AnalisisInversion.objects.update_or_create(
            propiedad=propiedad,
            defaults={
                'valor_terreno_estimado': valoracion['valor_terreno_estimado'],
                'valor_construccion_estimado': valoracion['valor_construccion_estimado'],
                'valor_total_estimado': valoracion['valor_total_estimado'],
                'gastos_notariales': costos['gastos_notariales'],
                'impuestos': costos['impuestos'],
                'comisiones': costos['comisiones'],
                'reparaciones': costos['reparaciones'],
                'otros_gastos': costos['otros_gastos'],
                'nivel_remodelacion_aplicado': remodelacion['nivel_obra'],
                'costo_remodelacion_m2': remodelacion['costo_m2'],
                'presupuesto_remodelacion': remodelacion['presupuesto'],
                'remodelacion_estimada': remodelacion['es_estimado'],
                'inversion_total': metricas['inversion_total'],
                'utilidad_potencial': metricas['utilidad_potencial'],
                'descuento_mercado': metricas['descuento_mercado'],
                'roi': metricas['roi'],
                'roi_anualizado': metricas['roi_anualizado'],
                'anos_recuperacion': metricas['anos_recuperacion'],
                'tasa_bancaria_referencia': config['tasa_bancaria'],
                'semaforo': semaforo,
                'es_oportunidad': es_oportunidad,
                'es_prioritaria': es_prioritaria,
                'datos_completos': valoracion['datos_completos'],
                'factor_estado_fisico': valoracion['factor_estado_fisico'],
                'factor_antiguedad': valoracion['factor_antiguedad'],
                'factor_ubicacion': valoracion['factor_ubicacion'],
                'factor_riesgo': valoracion['factor_riesgo'],
                'riesgos': '; '.join(riesgos) if riesgos else 'Sin riesgos significativos detectados',
                'recomendacion': recomendacion,
            },
        )

        propiedad.semaforo = semaforo
        if es_oportunidad and propiedad.estatus == 'nueva':
            propiedad.estatus = 'oportunidad'
        propiedad.save(update_fields=['semaforo', 'estatus'])

        from services.alerta import AlertaService
        if es_oportunidad:
            AlertaService.notificar_oportunidad(propiedad, analisis)

        return analisis