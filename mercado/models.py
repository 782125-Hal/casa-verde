from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.choices import (
    ESTADO_FISICO_CHOICES,
    NIVEL_REMODELACION_CHOICES,
    TIPO_INMUEBLE_CHOICES,
)
from geografia.models import ZonaMercado


class FuenteDatos(models.Model):
    nombre = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=[
        ('portal', 'Portal inmobiliario'),
        ('red_social', 'Red social'),
        ('agencia', 'Agencia inmobiliaria'),
        ('avaluo', 'Fuente de avalúo'),
        ('manual', 'Captura manual'),
        ('otro', 'Otro'),
    ])
    url_base = models.URLField(blank=True)
    activa = models.BooleanField(default=True)
    requiere_api = models.BooleanField(default=False)
    terminos_uso = models.TextField(blank=True, help_text='Notas sobre restricciones legales')
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Fuente de datos'
        verbose_name_plural = 'Fuentes de datos'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class ValorMetroCuadrado(models.Model):
    zona = models.ForeignKey(ZonaMercado, on_delete=models.CASCADE, related_name='valores_m2')
    tipo_inmueble = models.CharField(max_length=20, choices=TIPO_INMUEBLE_CHOICES)
    valor_terreno_m2 = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text='Valor promedio por m² de terreno (MXN)',
    )
    valor_construccion_m2 = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text='Valor promedio por m² construido (MXN)',
    )
    valor_min = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    valor_promedio = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    valor_max = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    antiguedad_anos = models.PositiveSmallIntegerField(null=True, blank=True)
    estado_fisico = models.CharField(max_length=20, choices=ESTADO_FISICO_CHOICES, blank=True)
    servicios = models.TextField(blank=True, help_text='Agua, luz, drenaje, gas, etc.')
    uso_suelo = models.CharField(max_length=100, blank=True)
    fecha_actualizacion = models.DateField()
    fuente = models.ForeignKey(
        FuenteDatos, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='valores_referencia',
    )
    confiabilidad = models.PositiveSmallIntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='1=baja, 5=alta confiabilidad',
    )
    notas = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Valor por metro cuadrado'
        verbose_name_plural = 'Valores por metro cuadrado'
        ordering = ['-fecha_actualizacion']
        indexes = [
            models.Index(fields=['zona', 'tipo_inmueble', '-fecha_actualizacion']),
        ]

    def __str__(self):
        return f'{self.zona} — {self.get_tipo_inmueble_display()} ({self.fecha_actualizacion})'


class TasaReferenciaBancaria(models.Model):
    institucion = models.CharField(max_length=150, default='Promedio bancario')
    tasa_anual = models.DecimalField(
        max_digits=5, decimal_places=2,
        help_text='Tasa de ahorro anual en %',
    )
    fecha_vigencia = models.DateField()
    fuente = models.CharField(max_length=200, blank=True)
    es_default = models.BooleanField(default=False)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Tasa de referencia bancaria'
        verbose_name_plural = 'Tasas de referencia bancaria'
        ordering = ['-fecha_vigencia']

    def __str__(self):
        return f'{self.institucion}: {self.tasa_anual}% ({self.fecha_vigencia})'

    def save(self, *args, **kwargs):
        if self.es_default:
            TasaReferenciaBancaria.objects.filter(es_default=True).update(es_default=False)
        super().save(*args, **kwargs)

    @classmethod
    def obtener_tasa_vigente(cls):
        tasa = cls.objects.filter(es_default=True).first()
        if tasa:
            return tasa.tasa_anual
        ultima = cls.objects.order_by('-fecha_vigencia').first()
        if ultima:
            return ultima.tasa_anual
        from core.choices import DEFAULT_TASA_BANCARIA
        from decimal import Decimal
        return Decimal(str(DEFAULT_TASA_BANCARIA))


class ScrapeEjecucion(models.Model):
    ESTADO_CHOICES = [
        ('en_proceso', 'En proceso'),
        ('completado', 'Completado'),
        ('error', 'Error'),
        ('omitido', 'Omitido'),
    ]

    configuracion = models.ForeignKey(
        'analisis.ConfiguracionBusqueda', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='scrapes',
    )
    fuente = models.ForeignKey(FuenteDatos, on_delete=models.CASCADE, related_name='ejecuciones')
    zona = models.ForeignKey(ZonaMercado, on_delete=models.CASCADE, related_name='scrapes')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='en_proceso')
    encontrados = models.PositiveIntegerField(default=0)
    nuevos = models.PositiveIntegerField(default=0)
    actualizados = models.PositiveIntegerField(default=0)
    errores = models.PositiveIntegerField(default=0)
    log = models.TextField(blank=True)
    iniciado_en = models.DateTimeField(auto_now_add=True)
    finalizado_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Ejecución de scraping'
        verbose_name_plural = 'Ejecuciones de scraping'
        ordering = ['-iniciado_en']

    def __str__(self):
        return f'{self.fuente.nombre} — {self.zona.nombre} ({self.get_estado_display()})'


class ComparativoMercado(models.Model):
    zona = models.ForeignKey(ZonaMercado, on_delete=models.CASCADE, related_name='comparativos')
    tipo_inmueble = models.CharField(max_length=20, choices=TIPO_INMUEBLE_CHOICES)
    precio_promedio_m2 = models.DecimalField(max_digits=12, decimal_places=2)
    total_propiedades = models.PositiveIntegerField(default=0)
    periodo = models.DateField(help_text='Inicio del periodo analizado')
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Comparativo de mercado'
        verbose_name_plural = 'Comparativos de mercado'
        ordering = ['-periodo']

    def __str__(self):
        return f'{self.zona} — {self.get_tipo_inmueble_display()} ({self.periodo})'


class CostoRemodelacionM2(models.Model):
    """
    Costo de remodelación por m² de construcción, por zona y nivel de obra.

    Alimenta el presupuesto de remodelación que se descuenta en el análisis
    de inversión (RemodelacionService). Cada zona puede tener su propio costo;
    si una zona no tiene registro para un nivel, el sistema recurre al fallback
    global (core.choices.DEFAULT_COSTO_REMODELACION_M2).
    """
    zona = models.ForeignKey(
        ZonaMercado, on_delete=models.CASCADE, related_name='costos_remodelacion',
    )
    nivel_obra = models.CharField(max_length=20, choices=NIVEL_REMODELACION_CHOICES)
    costo_m2 = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text='Costo de remodelación por m² de construcción (MXN)',
    )
    fecha_actualizacion = models.DateField()
    fuente = models.ForeignKey(
        FuenteDatos, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='costos_remodelacion',
    )
    confiabilidad = models.PositiveSmallIntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='1=baja, 5=alta confiabilidad',
    )
    notas = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Costo de remodelación por m²'
        verbose_name_plural = 'Costos de remodelación por m²'
        ordering = ['zona', 'nivel_obra', '-fecha_actualizacion']
        indexes = [
            models.Index(fields=['zona', 'nivel_obra', '-fecha_actualizacion']),
        ]

    def __str__(self):
        return f'{self.zona} — {self.get_nivel_obra_display()}: ${self.costo_m2:,.0f}/m²'

    @classmethod
    def obtener_costo_m2(cls, zona, nivel_obra):
        """
        Devuelve el costo/m² más reciente para (zona, nivel_obra), o None
        si la zona no tiene ese nivel capturado.
        """
        registro = cls.objects.filter(
            zona=zona, nivel_obra=nivel_obra,
        ).order_by('-fecha_actualizacion').first()
        return registro.costo_m2 if registro else None