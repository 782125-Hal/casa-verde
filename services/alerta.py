"""Servicio de alertas — Casa Verde (Fase 5)."""
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils import timezone

from alertas.models import Alerta

logger = logging.getLogger(__name__)


class AlertaService:
    """Genera y envía alertas por oportunidades detectadas."""

    @classmethod
    def _usuarios_para_zona(cls, zona):
        User = get_user_model()
        return User.objects.filter(
            is_active=True,
            busquedas__zona=zona,
            busquedas__activa=True,
        ).distinct()

    @classmethod
    def _usuarios_inversionistas(cls):
        User = get_user_model()
        return User.objects.filter(
            is_active=True,
            rol__in=['administrador', 'analista', 'inversionista'],
        )

    @classmethod
    def _debe_alertar(cls, usuario, analisis=None):
        if usuario.alertas_solo_prioritarias and analisis:
            return analisis.es_prioritaria
        return True

    @classmethod
    def crear_alerta(cls, usuario, propiedad, tipo, mensaje, canal='interna'):
        existe = Alerta.objects.filter(
            usuario=usuario,
            propiedad=propiedad,
            tipo=tipo,
            leida=False,
        ).exists()
        if existe:
            return None

        return Alerta.objects.create(
            usuario=usuario,
            propiedad=propiedad,
            tipo=tipo,
            canal=canal,
            mensaje=mensaje,
        )

    @classmethod
    def notificar_oportunidad(cls, propiedad, analisis):
        if not analisis.es_oportunidad:
            return []

        usuarios = cls._usuarios_para_zona(propiedad.zona)
        if not usuarios.exists():
            usuarios = cls._usuarios_inversionistas()

        tipo = 'nueva_oportunidad' if analisis.es_prioritaria else 'descuento_relevante'
        etiqueta = 'OPORTUNIDAD PRIORITARIA' if analisis.es_prioritaria else 'Oportunidad detectada'
        mensaje = (
            f'{etiqueta} en {propiedad.zona.nombre}\n'
            f'{propiedad.titulo}\n'
            f'Precio: ${propiedad.precio_publicado:,.0f}\n'
            f'Descuento: {analisis.descuento_mercado:.1f}% | ROI anual: {analisis.roi_anualizado:.1f}%'
        )
        if propiedad.url_anuncio:
            mensaje += f'\n{propiedad.url_anuncio}'

        alertas = []
        for usuario in usuarios:
            if not cls._debe_alertar(usuario, analisis):
                continue
            alerta = cls.crear_alerta(usuario, propiedad, tipo, mensaje)
            if alerta:
                alertas.append(alerta)
                cls._enviar(alerta, usuario)

        return alertas

    @classmethod
    def notificar_baja_precio(cls, propiedad, precio_anterior):
        usuarios = cls._usuarios_para_zona(propiedad.zona)
        if not usuarios.exists():
            usuarios = cls._usuarios_inversionistas()

        reduccion = ((precio_anterior - propiedad.precio_publicado) / precio_anterior) * 100
        mensaje = (
            f'Baja de precio en {propiedad.zona.nombre}\n'
            f'{propiedad.titulo}\n'
            f'${precio_anterior:,.0f} → ${propiedad.precio_publicado:,.0f} ({reduccion:.1f}% menos)'
        )

        alertas = []
        for usuario in usuarios:
            alerta = cls.crear_alerta(usuario, propiedad, 'baja_precio', mensaje)
            if alerta:
                alertas.append(alerta)
                cls._enviar(alerta, usuario)
        return alertas

    @classmethod
    def _enviar(cls, alerta, usuario):
        canales_enviados = ['interna']

        pref = usuario.canal_alerta_preferido
        enviar_email = (
            usuario.notificaciones_email
            and pref in ('email', 'email_telegram')
        )
        enviar_telegram = (
            usuario.notificaciones_telegram
            and usuario.telegram_chat_id
            and pref in ('telegram', 'email_telegram')
        )

        if enviar_email:
            if cls._enviar_email(alerta, usuario):
                canales_enviados.append('email')

        if enviar_telegram:
            if cls._enviar_telegram(alerta, usuario):
                canales_enviados.append('telegram')

        alerta.enviada = True
        alerta.fecha_envio = timezone.now()
        alerta.canal = canales_enviados[-1] if len(canales_enviados) > 1 else 'interna'
        alerta.save(update_fields=['enviada', 'fecha_envio', 'canal'])

    @classmethod
    def _enviar_email(cls, alerta, usuario):
        if not usuario.email:
            return False
        try:
            site = getattr(settings, 'CASA_VERDE', {}).get('NOMBRE', 'Casa Verde')
            send_mail(
                subject=f'[{site}] {alerta.get_tipo_display()}',
                message=alerta.mensaje,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'casaverde@localhost'),
                recipient_list=[usuario.email],
                fail_silently=False,
            )
            return True
        except Exception as exc:
            logger.warning('Email falló para %s: %s', usuario.email, exc)
            return False

    @classmethod
    def _enviar_telegram(cls, alerta, usuario):
        from services.telegram import enviar_mensaje, telegram_configurado
        if not telegram_configurado():
            return False
        site = getattr(settings, 'CASA_VERDE', {}).get('NOMBRE', 'Casa Verde')
        texto = f'<b>{site}</b>\n<b>{alerta.get_tipo_display()}</b>\n\n{alerta.mensaje}'
        return enviar_mensaje(usuario.telegram_chat_id, texto)

    @classmethod
    def enviar_prueba(cls, usuario):
        """Envía alerta de prueba al usuario según su canal configurado."""
        mensaje = (
            f'Alerta de prueba — {getattr(settings, "CASA_VERDE", {}).get("NOMBRE", "Casa Verde")}\n'
            'Si recibes este mensaje, las notificaciones están configuradas correctamente.'
        )
        alerta = Alerta.objects.create(
            usuario=usuario,
            tipo='nueva_oportunidad',
            canal='interna',
            mensaje=mensaje,
            enviada=False,
        )
        cls._enviar(alerta, usuario)
        return alerta