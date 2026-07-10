from django.db import models


class Estado(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    clave = models.CharField(max_length=5, unique=True, help_text='Clave INEGI')

    class Meta:
        verbose_name = 'Estado'
        verbose_name_plural = 'Estados'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Municipio(models.Model):
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE, related_name='municipios')
    nombre = models.CharField(max_length=150)

    class Meta:
        verbose_name = 'Municipio'
        verbose_name_plural = 'Municipios'
        ordering = ['nombre']
        unique_together = ['estado', 'nombre']

    def __str__(self):
        return f'{self.nombre}, {self.estado.nombre}'


class ZonaMercado(models.Model):
    municipio = models.ForeignKey(Municipio, on_delete=models.CASCADE, related_name='zonas')
    nombre = models.CharField(max_length=200, help_text='Nombre de la zona o colonia')
    colonia = models.CharField(max_length=200, blank=True)
    ciudad = models.CharField(max_length=150, blank=True)
    latitud = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitud = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    radio_metros = models.PositiveIntegerField(default=2000, help_text='Radio de búsqueda en metros')
    activa = models.BooleanField(default=True)
    creada_en = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Zona de mercado'
        verbose_name_plural = 'Zonas de mercado'
        ordering = ['municipio', 'nombre']

    def __str__(self):
        return f'{self.nombre} ({self.municipio})'

    @property
    def ubicacion_completa(self):
        partes = [self.nombre, self.colonia, self.ciudad, str(self.municipio)]
        return ', '.join(p for p in partes if p)