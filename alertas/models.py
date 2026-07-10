from django.db import models

from core.choices import CANAL_ALERTA_CHOICES, TIPO_ALERTA_CHOICES


class Alerta(models.Model):
    usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.CASCADE, related_name='alertas')
    propiedad = models.ForeignKey(
        'propiedades.Propiedad', on_delete=models.CASCADE,
        related_name='alertas', null=True, blank=True,
    )
    tipo = models.CharField(max_length=30, choices=TIPO_ALERTA_CHOICES)
    canal = models.CharField(max_length=20, choices=CANAL_ALERTA_CHOICES, default='interna')
    mensaje = models.TextField()
    enviada = models.BooleanField(default=False)
    leida = models.BooleanField(default=False)
    fecha_envio = models.DateTimeField(null=True, blank=True)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Alerta'
        verbose_name_plural = 'Alertas'
        ordering = ['-creada_en']

    def __str__(self):
        return f'{self.get_tipo_display()} — {self.usuario.username}'