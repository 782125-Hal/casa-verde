from django import forms

from analisis.models import ConfiguracionBusqueda
from core.choices import TIPO_INMUEBLE_CHOICES
from geografia.models import ZonaMercado


class ImportarCSVForm(forms.Form):
    archivo = forms.FileField(
        label='Archivo CSV',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv'}),
    )


class ImportarURLForm(forms.Form):
    url = forms.URLField(
        label='URL del anuncio',
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://www.lamudi.com.mx/...',
        }),
    )
    zona = forms.ModelChoiceField(
        queryset=ZonaMercado.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['zona'].queryset = ZonaMercado.objects.filter(
            activa=True, municipio__nombre='Tijuana',
        ).order_by('nombre')


class ConfiguracionBusquedaForm(forms.ModelForm):
    tipo_inmueble = forms.ChoiceField(
        choices=[('', 'Todos los tipos')] + list(TIPO_INMUEBLE_CHOICES),
        required=False,
    )

    class Meta:
        model = ConfiguracionBusqueda
        fields = ['zona', 'tipo_inmueble', 'radio_metros', 'descuento_minimo', 'frecuencia', 'activa']
        widgets = {
            'zona': forms.Select(attrs={'class': 'form-select'}),
            'tipo_inmueble': forms.Select(attrs={'class': 'form-select'}),
            'radio_metros': forms.NumberInput(attrs={'class': 'form-control'}),
            'descuento_minimo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'frecuencia': forms.Select(attrs={'class': 'form-select'}),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['zona'].queryset = ZonaMercado.objects.filter(
            activa=True,
            municipio__nombre='Tijuana',
        ).order_by('nombre')