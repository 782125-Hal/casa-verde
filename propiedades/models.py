from django.db import models

from core.choices import (
    ESTADO_FISICO_A_NIVEL_REMODELACION,
    ESTATUS_PROPIEDAD_CHOICES,
    ESTADO_FISICO_CHOICES,
    NIVEL_REMODELACION_CHOICES,
    SEMAFORO_CHOICES,
    TIPO_INMUEBLE_CHOICES,
)
from geografia.models import ZonaMercado
from mercado.models import FuenteDatos


class Propiedad(models.Model):
    zona = models.ForeignKey(ZonaMercado, on_delete=models.PROTECT, related_name='propiedades')
    fuente = models.ForeignKey(FuenteDatos, on_delete=models.SET_NULL, null=True, blank=True, related_name='propiedades')
    titulo = models.CharField(max_length=300)
    descripcion = models.TextField(blank=True)
    precio_publicado = models.DecimalField(max_digits=14, decimal_places=2, help_text='Precio en MXN')
    latitud = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitud = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    direccion = models.CharField(max_length=400, blank=True)
    m2_terreno = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    m2_construccion = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    habitaciones = models.PositiveSmallIntegerField(null=True, blank=True)
    banos = models.PositiveSmallIntegerField(null=True, blank=True)
    niveles = models.PositiveSmallIntegerField(null=True, blank=True)
    estacionamientos = models.PositiveSmallIntegerField(null=True, blank=True)
    antiguedad_anos = models.PositiveSmallIntegerField(null=True, blank=True)
    estado_fisico = models.CharField(max_length=20, choices=ESTADO_FISICO_CHOICES, default='regular')
    nivel_remodelacion = models.CharField(
        max_length=20, choices=NIVEL_REMODELACION_CHOICES, blank=True,
        help_text='Nivel de obra requerido. Si se deja vacío, se deriva del estado físico.',
    )
    tipo_inmueble = models.CharField(max_length=20, choices=TIPO_INMUEBLE_CHOICES)
    url_anuncio = models.URLField(blank=True)
    imagen_url = models.URLField(blank=True, help_text='Enlace público a fotografía')
    contacto_publico = models.CharField(max_length=200, blank=True, help_text='Solo si es público y permitido')
    fecha_publicacion = models.DateField(null=True, blank=True)
    fecha_deteccion = models.DateTimeField(auto_now_add=True)
    estatus = models.CharField(max_length=20, choices=ESTATUS_PROPIEDAD_CHOICES, default='nueva')
    semaforo = models.CharField(max_length=10, choices=SEMAFORO_CHOICES, default='gris')
    riesgo_documental = models.PositiveSmallIntegerField(default=2, help_text='1=muy bajo, 5=muy alto')
    riesgo_legal = models.PositiveSmallIntegerField(default=2)
    riesgo_fisico = models.PositiveSmallIntegerField(default=2)
    capturado_por = models.ForeignKey(
        'usuarios.Usuario', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='propiedades_capturadas',
    )
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Propiedad'
        verbose_name_plural = 'Propiedades'
        ordering = ['-fecha_deteccion']
        indexes = [
            models.Index(fields=['zona', 'estatus', 'semaforo']),
            models.Index(fields=['precio_publicado', '-fecha_deteccion']),
        ]

    def __str__(self):
        return f'{self.titulo} — ${self.precio_publicado:,.0f}'

    @property
    def tiene_datos_minimos(self):
        tiene_superficie = bool(self.m2_terreno or self.m2_construccion)
        return bool(self.precio_publicado and self.zona_id and tiene_superficie)

    @property
    def precio_m2_terreno(self):
        if self.m2_terreno and self.m2_terreno > 0:
            return self.precio_publicado / self.m2_terreno
        return None

    @property
    def precio_m2_construccion(self):
        if self.m2_construccion and self.m2_construccion > 0:
            return self.precio_publicado / self.m2_construccion
        return None

    @property
    def riesgo_total(self):
        return max(self.riesgo_documental, self.riesgo_legal, self.riesgo_fisico)

    @property
    def nivel_remodelacion_efectivo(self):
        """
        Nivel de obra a usar en el análisis: el capturado explícitamente, o el
        derivado del estado físico si no se capturó ninguno.
        """
        if self.nivel_remodelacion:
            return self.nivel_remodelacion
        return ESTADO_FISICO_A_NIVEL_REMODELACION.get(self.estado_fisico, 'media')


class HistorialPrecio(models.Model):
    propiedad = models.ForeignKey(Propiedad, on_delete=models.CASCADE, related_name='historial_precios')
    precio_anterior = models.DecimalField(max_digits=14, decimal_places=2)
    precio_nuevo = models.DecimalField(max_digits=14, decimal_places=2)
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    motivo = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = 'Historial de precio'
        verbose_name_plural = 'Historial de precios'
        ordering = ['-fecha_cambio']

    def __str__(self):
        return f'{self.propiedad_id}: ${self.precio_anterior:,.0f} → ${self.precio_nuevo:,.0f}'

    @property
    def variacion_porcentaje(self):
        if self.precio_anterior > 0:
            return ((self.precio_nuevo - self.precio_anterior) / self.precio_anterior) * 100
        return 0