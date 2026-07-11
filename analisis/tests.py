"""
Pruebas del estimador de presupuesto de remodelación y su integración
con el análisis de inversión — Casa Verde.
"""
from datetime import date
from decimal import Decimal

from django.test import TestCase

from analisis.models import AnalisisInversion
from geografia.models import Estado, Municipio, ZonaMercado
from mercado.models import (
    CostoRemodelacionM2,
    TasaReferenciaBancaria,
    ValorMetroCuadrado,
)
from propiedades.models import Propiedad
from services.oportunidad import OportunidadService
from services.remodelacion import RemodelacionService


class BaseDatosMixin:
    """Crea geografía, valores de mercado y tasa base para las pruebas."""

    def _crear_base(self):
        estado = Estado.objects.create(nombre='Baja California', clave='BC')
        municipio = Municipio.objects.create(estado=estado, nombre='Tijuana')
        self.zona = ZonaMercado.objects.create(
            municipio=municipio, nombre='La Mesa', ciudad='Tijuana',
        )
        ValorMetroCuadrado.objects.create(
            zona=self.zona, tipo_inmueble='casa',
            valor_terreno_m2=Decimal('6000'),
            valor_construccion_m2=Decimal('15000'),
            fecha_actualizacion=date.today(),
        )
        TasaReferenciaBancaria.objects.create(
            institucion='Base', tasa_anual=Decimal('4.5'),
            fecha_vigencia=date.today(), es_default=True,
        )

    def _propiedad(self, **kwargs):
        defaults = dict(
            zona=self.zona,
            titulo='Casa de prueba',
            precio_publicado=Decimal('2000000'),
            m2_terreno=Decimal('150'),
            m2_construccion=Decimal('120'),
            tipo_inmueble='casa',
            estado_fisico='regular',
        )
        defaults.update(kwargs)
        return Propiedad.objects.create(**defaults)


class RemodelacionServiceTests(BaseDatosMixin, TestCase):
    def setUp(self):
        self._crear_base()

    def test_usa_costo_de_zona_cuando_existe(self):
        CostoRemodelacionM2.objects.create(
            zona=self.zona, nivel_obra='media',
            costo_m2=Decimal('6000'), fecha_actualizacion=date.today(),
        )
        prop = self._propiedad(estado_fisico='regular')  # regular -> media
        r = RemodelacionService.estimar(prop)

        self.assertEqual(r['nivel_obra'], 'media')
        self.assertEqual(r['costo_m2'], Decimal('6000.00'))
        self.assertEqual(r['m2_base'], Decimal('120.00'))
        self.assertEqual(r['presupuesto'], Decimal('720000.00'))  # 120 * 6000
        self.assertFalse(r['es_estimado'])

    def test_fallback_global_cuando_zona_sin_costo(self):
        prop = self._propiedad(estado_fisico='malo')  # malo -> completa (12000)
        r = RemodelacionService.estimar(prop)

        self.assertEqual(r['nivel_obra'], 'completa')
        self.assertEqual(r['costo_m2'], Decimal('12000.00'))
        self.assertEqual(r['presupuesto'], Decimal('1440000.00'))  # 120 * 12000
        self.assertTrue(r['es_estimado'])

    def test_override_manual_tiene_prioridad_sobre_estado(self):
        prop = self._propiedad(estado_fisico='malo', nivel_remodelacion='ligera')
        r = RemodelacionService.estimar(prop)
        self.assertEqual(r['nivel_obra'], 'ligera')
        self.assertEqual(r['presupuesto'], Decimal('300000.00'))  # 120 * 2500

    def test_estado_excelente_no_genera_presupuesto(self):
        prop = self._propiedad(estado_fisico='excelente')  # -> ninguna
        r = RemodelacionService.estimar(prop)
        self.assertEqual(r['nivel_obra'], 'ninguna')
        self.assertEqual(r['presupuesto'], Decimal('0'))

    def test_terreno_sin_construccion_no_genera_presupuesto(self):
        prop = self._propiedad(
            tipo_inmueble='terreno', m2_construccion=None, estado_fisico='malo',
        )
        r = RemodelacionService.estimar(prop)
        self.assertEqual(r['presupuesto'], Decimal('0'))


class IntegracionAnalisisTests(BaseDatosMixin, TestCase):
    def setUp(self):
        self._crear_base()

    def test_presupuesto_se_descuenta_en_el_analisis(self):
        CostoRemodelacionM2.objects.create(
            zona=self.zona, nivel_obra='media',
            costo_m2=Decimal('6000'), fecha_actualizacion=date.today(),
        )
        prop = self._propiedad(estado_fisico='regular')
        analisis = OportunidadService.analizar_propiedad(prop)

        self.assertEqual(analisis.presupuesto_remodelacion, Decimal('720000.00'))
        self.assertEqual(analisis.nivel_remodelacion_aplicado, 'media')
        self.assertEqual(analisis.costo_remodelacion_m2, Decimal('6000.00'))
        self.assertFalse(analisis.remodelacion_estimada)
        # La partida reparaciones debe reflejar el presupuesto de remodelación.
        self.assertEqual(analisis.reparaciones, Decimal('720000.00'))
        # Y estar incluida en la inversión total.
        self.assertGreaterEqual(analisis.inversion_total, prop.precio_publicado + analisis.reparaciones)

    def test_analisis_con_usuario_de_config_float_no_falla(self):
        """
        Regresión: un Usuario recién creado tiene descuento_minimo/tasa como
        float (valor por defecto en memoria). El análisis no debe romper al
        mezclar float con Decimal en determinar_semaforo.
        """
        from usuarios.models import Usuario
        usuario = Usuario.objects.create(username='inv_prueba')
        prop = self._propiedad(estado_fisico='regular', capturado_por=usuario)
        # No debe lanzar TypeError:
        analisis = OportunidadService.analizar_propiedad(prop, usuario=usuario)
        self.assertIsNotNone(analisis.semaforo)

    def test_mas_remodelacion_reduce_utilidad_y_roi(self):
        """A mayor nivel de obra, menor utilidad y ROI (todo lo demás igual)."""
        prop_ligera = self._propiedad(estado_fisico='regular', nivel_remodelacion='ligera')
        prop_completa = self._propiedad(estado_fisico='regular', nivel_remodelacion='completa')

        a_ligera = OportunidadService.analizar_propiedad(prop_ligera)
        a_completa = OportunidadService.analizar_propiedad(prop_completa)

        self.assertGreater(a_completa.reparaciones, a_ligera.reparaciones)
        self.assertLess(a_completa.utilidad_potencial, a_ligera.utilidad_potencial)
        self.assertLess(a_completa.roi, a_ligera.roi)
