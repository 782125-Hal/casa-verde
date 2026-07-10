from django.contrib.auth.models import AbstractUser
from django.db import models

from core.choices import (
    CANAL_PREFERIDO_CHOICES,
    DEFAULT_DESCUENTO_MINIMO,
    DEFAULT_PLAZO_RECUPERACION,
    DEFAULT_RIESGO_MAXIMO,
    DEFAULT_TASA_BANCARIA,
    ROL_USUARIO_CHOICES,
)


class Usuario(AbstractUser):
    rol = models.CharField(max_length=20, choices=ROL_USUARIO_CHOICES, default='inversionista')
    telefono = models.CharField(max_length=20, blank=True)
    tasa_ahorro_personal = models.DecimalField(
        max_digits=5, decimal_places=2,
        default=DEFAULT_TASA_BANCARIA,
        help_text='Tasa bancaria de ahorro personal (%)',
    )
    descuento_minimo = models.DecimalField(
        max_digits=5, decimal_places=2,
        default=DEFAULT_DESCUENTO_MINIMO,
        help_text='Descuento mínimo para considerar oportunidad (%)',
    )
    plazo_recuperacion_max = models.PositiveSmallIntegerField(
        default=DEFAULT_PLAZO_RECUPERACION,
        help_text='Plazo máximo de recuperación en años',
    )
    riesgo_maximo = models.PositiveSmallIntegerField(
        default=DEFAULT_RIESGO_MAXIMO,
        help_text='Nivel máximo de riesgo aceptable (1-5)',
    )
    canal_alerta_preferido = models.CharField(
        max_length=20, choices=CANAL_PREFERIDO_CHOICES, default='email',
        help_text='Canal principal de alertas',
    )
    notificaciones_email = models.BooleanField(default=True)
    notificaciones_telegram = models.BooleanField(default=False)
    telegram_chat_id = models.CharField(
        max_length=50, blank=True,
        help_text='ID de chat de Telegram (obtener con @userinfobot)',
    )
    notificaciones_whatsapp = models.BooleanField(
        default=False,
        help_text='WhatsApp vía Twilio — tiene costo por mensaje',
    )
    alertas_solo_prioritarias = models.BooleanField(
        default=False,
        help_text='Solo alertar oportunidades verdes/prioritarias',
    )

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_rol_display()})'

    @property
    def es_administrador(self):
        return self.rol == 'administrador' or self.is_superuser

    @property
    def puede_capturar(self):
        return self.rol in ('administrador', 'analista', 'capturista') or self.is_superuser

    @property
    def puede_analizar(self):
        return self.rol in ('administrador', 'analista') or self.is_superuser

    @property
    def solo_lectura(self):
        return self.rol == 'consulta'