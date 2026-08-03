"""Formularios del módulo de presupuestos."""
from django import forms

from presupuestos.choices import DEFAULT_PCT_CONTINGENCIA
from presupuestos.models import PartidaPresupuesto, Presupuesto
from presupuestos.plantillas import PLANTILLA_CHOICES
from propiedades.models import Propiedad

_SELECT = {'class': 'form-select'}
_INPUT = {'class': 'form-control'}


class PresupuestoForm(forms.ModelForm):
    """Encabezado: identificación + los % de las capas."""

    class Meta:
        model = Presupuesto
        fields = [
            'nombre', 'propiedad', 'tipo_obra', 'estado', 'area_m2',
            'pct_indirectos', 'pct_contingencia', 'pct_utilidad',
            'aplica_iva', 'pct_iva', 'es_activo', 'notas',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={**_INPUT, 'placeholder': 'Ej. Remodelación integral — escenario base'}),
            'propiedad': forms.Select(attrs=_SELECT),
            'tipo_obra': forms.Select(attrs=_SELECT),
            'estado': forms.Select(attrs=_SELECT),
            'area_m2': forms.NumberInput(attrs={**_INPUT, 'step': '0.01', 'min': '0'}),
            'pct_indirectos': forms.NumberInput(attrs={**_INPUT, 'step': '0.01', 'min': '0'}),
            'pct_contingencia': forms.NumberInput(attrs={**_INPUT, 'step': '0.01', 'min': '0'}),
            'pct_utilidad': forms.NumberInput(attrs={**_INPUT, 'step': '0.01', 'min': '0'}),
            'pct_iva': forms.NumberInput(attrs={**_INPUT, 'step': '0.01', 'min': '0'}),
            'aplica_iva': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'es_activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notas': forms.Textarea(attrs={**_INPUT, 'rows': 2}),
        }
        help_texts = {
            'pct_contingencia': 'Reserva para imprevistos REALES, no para mejoras.',
            'es_activo': 'El que alimentará el ROI de la propiedad (Fase 3).',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['propiedad'].queryset = (
            Propiedad.objects.select_related('zona').order_by('titulo')
        )
        self.fields['propiedad'].required = False
        self.fields['propiedad'].empty_label = 'Sin propiedad ligada'

    def clean(self):
        """Un solo presupuesto activo por propiedad.

        El modelo ya lo impide con una UniqueConstraint, pero eso sale como
        IntegrityError; aquí se traduce a un error de formulario legible.
        """
        datos = super().clean()
        propiedad = datos.get('propiedad')
        if datos.get('es_activo') and propiedad:
            otros = Presupuesto.objects.filter(propiedad=propiedad, es_activo=True)
            if self.instance.pk:
                otros = otros.exclude(pk=self.instance.pk)
            if otros.exists():
                self.add_error('es_activo', forms.ValidationError(
                    'Esa propiedad ya tiene un presupuesto activo (%(nombre)s). '
                    'Desactívalo primero.',
                    params={'nombre': otros.first().nombre},
                ))
        return datos


class PresupuestoCrearForm(PresupuestoForm):
    """Alta: los mismos campos + la plantilla que precarga partidas (§3.3)."""

    plantilla = forms.ChoiceField(
        choices=PLANTILLA_CHOICES, required=False, label='Plantilla de partidas',
        widget=forms.Select(attrs=_SELECT),
        help_text='Precarga las partidas típicas con cantidad 0, para que solo ajustes cantidades.',
    )

    class Meta(PresupuestoForm.Meta):
        fields = [
            'nombre', 'propiedad', 'tipo_obra', 'area_m2',
            'pct_indirectos', 'pct_contingencia', 'pct_utilidad',
            'aplica_iva', 'pct_iva', 'notas',
        ]

    def clean(self):
        """Avisa si la plantilla no corresponde al tipo de obra elegido.

        No lo bloquea: puede haber casos mixtos (una obra nueva con partidas de
        remodelación de una construcción existente en el mismo predio).
        """
        datos = super().clean()
        from presupuestos.plantillas import PLANTILLAS

        clave = datos.get('plantilla')
        tipo = datos.get('tipo_obra')
        plantilla = PLANTILLAS.get(clave)
        if plantilla and tipo and plantilla['tipo_obra'] != tipo:
            self.add_error('plantilla', forms.ValidationError(
                'La plantilla «%(plantilla)s» es de %(suyo)s y elegiste %(tuyo)s. '
                'Cambia una de las dos.',
                params={
                    'plantilla': plantilla['nombre'],
                    'suyo': dict(self.fields['tipo_obra'].choices).get(plantilla['tipo_obra']),
                    'tuyo': dict(self.fields['tipo_obra'].choices).get(tipo),
                },
            ))
        return datos


class PartidaForm(forms.ModelForm):
    """Un renglón. El autocompletado del catálogo se resuelve en el template:
    al elegir un concepto se copian descripción, unidad y PU, y quedan editables
    (el precio del renglón se congela al armarlo, no se lee por la FK)."""

    class Meta:
        model = PartidaPresupuesto
        fields = ['concepto', 'categoria', 'descripcion', 'unidad', 'cantidad', 'pu', 'orden', 'notas']
        widgets = {
            'concepto': forms.HiddenInput(),
            'categoria': forms.Select(attrs=_SELECT),
            'descripcion': forms.TextInput(attrs={**_INPUT, 'placeholder': 'Descripción del concepto'}),
            'unidad': forms.Select(attrs=_SELECT),
            'cantidad': forms.NumberInput(attrs={**_INPUT, 'step': '0.01', 'min': '0'}),
            'pu': forms.NumberInput(attrs={**_INPUT, 'step': '0.01', 'min': '0'}),
            'orden': forms.NumberInput(attrs={**_INPUT, 'min': '0'}),
            'notas': forms.Textarea(attrs={**_INPUT, 'rows': 2}),
        }
