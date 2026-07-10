from django.db import models

from core.choices import NIVEL_REMODELACION_CHOICES, SEMAFORO_CHOICES, TIPO_INMUEBLE_CHOICES
from geografia.models import ZonaMercado
from propiedades.models import Propiedad


class ConfiguracionBusqueda(models.Model):
    FRECUENCIA_CHOICES = [
        ('diaria', 'Diaria'),
        ('semanal', 'Semanal'),
        ('quincenal', 'Quincenal'),
        ('mensual', 'Mensual'),
    ]

    usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.CASCADE, related_name='busquedas')
    zona = models.ForeignKey(ZonaMercado, on_delete=models.CASCADE, related_name='busquedas')
    tipo_inmueble = models.CharField(max_length=20, choices=TIPO_INMUEBLE_CHOICES, blank=True)
    radio_metros = models.PositiveIntegerField(default=2000)
    descuento_minimo = models.DecimalField(max_digits=5, decimal_places=2, default=15)
    activa = models.BooleanField(default=True)
    frecuencia = models.CharField(max_length=20, choices=FRECUENCIA_CHOICES, default='semanal')
    ultima_ejecucion = models.DateTimeField(null=True, blank=True)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Configuración de búsqueda'
        verbose_name_plural = 'Configuraciones de búsqueda'
        ordering = ['-activa', '-creada_en']

    def __str__(self):
        tipo = self.get_tipo_inmueble_display() if self.tipo_inmueble else 'Todos'
        return f'{self.usuario.username} — {self.zona} ({tipo})'


class AnalisisInversion(models.Model):
    propiedad = models.OneToOneField(Propiedad, on_delete=models.CASCADE, related_name='analisis')
    analista = models.ForeignKey(
        'usuarios.Usuario', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='analisis_realizados',
    )

    # Valoración
    valor_terreno_estimado = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    valor_construccion_estimado = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    valor_total_estimado = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    # Costos adicionales
    gastos_notariales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    impuestos = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    comisiones = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reparaciones = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text='Presupuesto de remodelación (ver desglose abajo)',
    )
    otros_gastos = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Desglose del presupuesto de remodelación
    nivel_remodelacion_aplicado = models.CharField(
        max_length=20, choices=NIVEL_REMODELACION_CHOICES, blank=True,
        help_text='Nivel de obra usado para estimar el presupuesto',
    )
    costo_remodelacion_m2 = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text='Costo por m² aplicado (MXN)',
    )
    presupuesto_remodelacion = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        help_text='Presupuesto total de remodelación estimado (MXN)',
    )
    remodelacion_estimada = models.BooleanField(
        default=False,
        help_text='True si se usó el costo fallback global (la zona no tiene costo capturado)',
    )

    # Resultados financieros
    inversion_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    utilidad_potencial = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    descuento_mercado = models.DecimalField(max_digits=7, decimal_places=2, default=0, help_text='%')
    roi = models.DecimalField(max_digits=7, decimal_places=2, default=0, help_text='%')
    roi_anualizado = models.DecimalField(max_digits=7, decimal_places=2, default=0, help_text='%')
    anos_recuperacion = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tasa_bancaria_referencia = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Clasificación
    semaforo = models.CharField(max_length=10, choices=SEMAFORO_CHOICES, default='gris')
    es_oportunidad = models.BooleanField(default=False)
    es_prioritaria = models.BooleanField(default=False)
    datos_completos = models.BooleanField(default=False)

    # Factores aplicados
    factor_estado_fisico = models.DecimalField(max_digits=4, decimal_places=2, default=1.0)
    factor_antiguedad = models.DecimalField(max_digits=4, decimal_places=2, default=1.0)
    factor_ubicacion = models.DecimalField(max_digits=4, decimal_places=2, default=1.0)
    factor_riesgo = models.DecimalField(max_digits=4, decimal_places=2, default=1.0)

    riesgos = models.TextField(blank=True)
    recomendacion = models.TextField(blank=True)
    comentarios_analista = models.TextField(blank=True)
    calculado_en = models.DateTimeField(auto_now=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Análisis de inversión'
        verbose_name_plural = 'Análisis de inversión'
        ordering = ['-es_prioritaria', '-descuento_mercado']
        indexes = [
            models.Index(fields=['es_oportunidad', 'es_prioritaria', 'semaforo']),
        ]

    def __str__(self):
        return f'Análisis #{self.pk} — {self.propiedad.titulo[:40]}'

    @property
    def supera_tasa_bancaria(self):
        return self.roi_anualizado > self.tasa_bancaria_referencia