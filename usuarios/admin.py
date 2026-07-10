from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from usuarios.models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ['username', 'email', 'rol', 'descuento_minimo', 'tasa_ahorro_personal', 'is_active']
    list_filter = ['rol', 'is_active', 'notificaciones_email']
    fieldsets = UserAdmin.fieldsets + (
        ('Casa Verde — Perfil de inversión', {
            'fields': (
                'rol', 'telefono',
                'tasa_ahorro_personal', 'descuento_minimo',
                'plazo_recuperacion_max', 'riesgo_maximo',
            ),
        }),
        ('Alertas', {
            'fields': (
                'canal_alerta_preferido', 'notificaciones_email',
                'notificaciones_telegram', 'telegram_chat_id',
                'alertas_solo_prioritarias', 'notificaciones_whatsapp',
            ),
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Casa Verde', {'fields': ('rol',)}),
    )