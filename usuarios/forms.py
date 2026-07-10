from django import forms

from core.choices import CANAL_PREFERIDO_CHOICES
from usuarios.models import Usuario


class PreferenciasAlertaForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = [
            'canal_alerta_preferido',
            'notificaciones_email',
            'notificaciones_telegram',
            'telegram_chat_id',
            'notificaciones_whatsapp',
            'alertas_solo_prioritarias',
        ]
        widgets = {
            'canal_alerta_preferido': forms.Select(attrs={'class': 'form-select'}),
            'telegram_chat_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 123456789',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['canal_alerta_preferido'].choices = CANAL_PREFERIDO_CHOICES
        self.fields['notificaciones_whatsapp'].disabled = True
        self.fields['notificaciones_whatsapp'].help_text = (
            'WhatsApp requiere Twilio (~$0.05 USD/mensaje). No recomendado para alertas frecuentes.'
        )