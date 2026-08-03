"""Admin del módulo de presupuestos.

Fase 1: el admin ES la interfaz de captura, así que carga con más peso del
habitual. Los totales calculados se exponen como columnas de solo lectura para
que el desglose de capas (§2.4) se vea sin abrir la futura pestaña.
"""

# El servidor corre Python 3.9: sin esto, una anotación como `Decimal | None`
# se evalúa al importar y truena con "unsupported operand type(s) for |".
from __future__ import annotations

from django.contrib import admin
from django.utils.html import format_html

from presupuestos.models import (
    CatalogoConcepto,
    OrdenCambio,
    PartidaPresupuesto,
    Presupuesto,
    RegistroGasto,
)

_COLOR_SEMAFORO = {
    'verde': '#1a7f37', 'amarillo': '#bf8700', 'rojo': '#cf222e', 'gris': '#6e7781',
}


def _pesos(valor) -> str:
    return f'${valor:,.2f}'


@admin.register(CatalogoConcepto)
class CatalogoConceptoAdmin(admin.ModelAdmin):
    list_display = [
        'codigo', 'descripcion', 'categoria', 'unidad',
        'pu_material', 'pu_mano_obra', 'pu_equipo', 'pu_total_col',
        'vigencia', 'activo',
    ]
    list_filter = ['categoria', 'unidad', 'activo', 'vigencia']
    search_fields = ['codigo', 'descripcion', 'notas']
    list_editable = ['activo']
    ordering = ['categoria', 'codigo']
    readonly_fields = ['pu_total_col', 'actualizado_en']
    fieldsets = (
        ('Identificación', {'fields': ('codigo', 'descripcion', 'categoria', 'unidad')}),
        ('Precio unitario', {
            'fields': ('pu_material', 'pu_mano_obra', 'pu_equipo', 'pu_total_col'),
            'description': 'PU = material + mano de obra + equipo (§2.3 del diseño).',
        }),
        ('Vigencia', {'fields': ('vigencia', 'activo', 'notas', 'actualizado_en')}),
    )

    @admin.display(description='PU total')
    def pu_total_col(self, obj):
        return _pesos(obj.pu_total)


class PartidaInline(admin.TabularInline):
    model = PartidaPresupuesto
    extra = 0
    fields = ['categoria', 'descripcion', 'unidad', 'cantidad', 'pu', 'importe_col', 'orden']
    readonly_fields = ['importe_col']
    autocomplete_fields = ['concepto']
    ordering = ['categoria', 'orden']

    @admin.display(description='Importe')
    def importe_col(self, obj):
        return _pesos(obj.importe) if obj.pk else '—'


class RegistroGastoInline(admin.TabularInline):
    model = RegistroGasto
    extra = 0
    fields = ['fecha', 'descripcion', 'partida', 'proveedor', 'importe_real', 'factura']
    ordering = ['-fecha']


class OrdenCambioInline(admin.TabularInline):
    model = OrdenCambio
    extra = 0
    fields = ['fecha', 'descripcion', 'importe', 'estado', 'aprobado_por']
    ordering = ['-fecha']


@admin.register(Presupuesto)
class PresupuestoAdmin(admin.ModelAdmin):
    list_display = [
        'nombre', 'propiedad', 'tipo_obra', 'estado',
        'subtotal_directo_col', 'total_col', 'gasto_real_col',
        'semaforo_col', 'es_activo', 'creado_en',
    ]
    list_filter = ['tipo_obra', 'estado', 'es_activo', 'aplica_iva', 'creado_en']
    search_fields = ['nombre', 'notas', 'propiedad__titulo', 'propiedad__direccion']
    list_editable = ['es_activo']
    autocomplete_fields = ['propiedad']
    date_hierarchy = 'creado_en'
    inlines = [PartidaInline, RegistroGastoInline, OrdenCambioInline]
    readonly_fields = ['desglose_col', 'creado_en', 'actualizado_en']
    fieldsets = (
        ('Identificación', {
            'fields': ('nombre', 'propiedad', 'tipo_obra', 'estado', 'es_activo'),
        }),
        ('Parámetros de cálculo', {
            'fields': (
                'area_m2', 'pct_indirectos', 'pct_contingencia', 'pct_utilidad',
                ('aplica_iva', 'pct_iva'),
            ),
            'description': (
                'Las capas se aplican EN CASCADA: la contingencia sobre '
                'directo+indirectos, y la utilidad sobre todo lo anterior (§2.4).'
            ),
        }),
        ('Desglose', {'fields': ('desglose_col',)}),
        ('Control', {'fields': ('notas', 'creado_por', 'creado_en', 'actualizado_en')}),
    )

    @admin.display(description='Directo')
    def subtotal_directo_col(self, obj):
        return _pesos(obj.subtotal_directo)

    @admin.display(description='Total')
    def total_col(self, obj):
        return _pesos(obj.total)

    @admin.display(description='Gasto real')
    def gasto_real_col(self, obj):
        return _pesos(obj.gasto_real)

    @admin.display(description='Semáforo')
    def semaforo_col(self, obj):
        semaforo = obj.semaforo
        return format_html(
            '<b style="color:{}">{}</b>', _COLOR_SEMAFORO[semaforo], semaforo.upper()
        )

    @admin.display(description='Capas del presupuesto')
    def desglose_col(self, obj):
        """El desglose §2.4 en el propio formulario: sin esto habría que sumar a mano."""
        if not obj.pk:
            return 'Guarda el presupuesto para ver el desglose.'
        filas = [
            ('Costo directo', obj.subtotal_directo),
            (f'+ Indirectos ({obj.pct_indirectos}%)', obj.monto_indirectos),
            (f'+ Contingencia ({obj.pct_contingencia}%)', obj.monto_contingencia),
            (f'+ Utilidad ({obj.pct_utilidad}%)', obj.monto_utilidad),
        ]
        if obj.aplica_iva:
            filas.append((f'+ IVA ({obj.pct_iva}%)', obj.monto_iva))
        cuerpo = ''.join(
            f'<tr><td style="padding:2px 18px 2px 0">{etiqueta}</td>'
            f'<td style="text-align:right">{_pesos(monto)}</td></tr>'
            for etiqueta, monto in filas
        )
        extra = ''
        if obj.costo_m2 is not None:
            extra = (
                f'<tr><td style="padding-top:6px">Costo por m²</td>'
                f'<td style="text-align:right;padding-top:6px">{_pesos(obj.costo_m2)}</td></tr>'
            )
        return format_html(
            '<table>{}<tr><td style="padding-top:6px"><b>TOTAL</b></td>'
            '<td style="text-align:right;padding-top:6px"><b>{}</b></td></tr>{}</table>',
            format_html(cuerpo), _pesos(obj.total), format_html(extra),
        )


@admin.register(PartidaPresupuesto)
class PartidaPresupuestoAdmin(admin.ModelAdmin):
    list_display = [
        'descripcion', 'presupuesto', 'categoria', 'unidad',
        'cantidad', 'pu', 'importe_col', 'gasto_real_col', 'desviacion_col',
    ]
    list_filter = ['categoria', 'unidad', 'presupuesto__tipo_obra', 'presupuesto__estado']
    search_fields = ['descripcion', 'notas', 'presupuesto__nombre', 'concepto__codigo']
    autocomplete_fields = ['presupuesto', 'concepto']
    ordering = ['presupuesto', 'categoria', 'orden']

    @admin.display(description='Importe')
    def importe_col(self, obj):
        return _pesos(obj.importe)

    @admin.display(description='Gasto real')
    def gasto_real_col(self, obj):
        return _pesos(obj.gasto_real)

    @admin.display(description='Desviación')
    def desviacion_col(self, obj):
        desviacion = obj.desviacion
        color = '#cf222e' if desviacion > 0 else '#1a7f37'
        return format_html('<span style="color:{}">{}</span>', color, _pesos(desviacion))


@admin.register(RegistroGasto)
class RegistroGastoAdmin(admin.ModelAdmin):
    list_display = [
        'fecha', 'descripcion', 'presupuesto', 'partida',
        'proveedor', 'importe_real', 'factura',
    ]
    list_filter = ['fecha', 'presupuesto__estado', 'presupuesto__tipo_obra']
    search_fields = ['descripcion', 'proveedor', 'factura', 'presupuesto__nombre']
    autocomplete_fields = ['presupuesto', 'partida']
    date_hierarchy = 'fecha'
    ordering = ['-fecha']


@admin.register(OrdenCambio)
class OrdenCambioAdmin(admin.ModelAdmin):
    list_display = [
        'fecha', 'descripcion', 'presupuesto', 'importe',
        'estado', 'aprobado_por', 'fecha_resolucion',
    ]
    list_filter = ['estado', 'fecha', 'presupuesto__tipo_obra']
    search_fields = ['descripcion', 'motivo', 'presupuesto__nombre']
    autocomplete_fields = ['presupuesto']
    list_editable = ['estado']
    date_hierarchy = 'fecha'
    ordering = ['-fecha']
    fieldsets = (
        ('Cambio solicitado', {'fields': ('presupuesto', 'fecha', 'descripcion', 'importe')}),
        ('Justificación', {
            'fields': ('motivo',),
            'description': 'Distinguir IMPREVISTO real de mejora: la contingencia '
                           'solo cubre lo primero (§4.1).',
        }),
        ('Resolución', {'fields': ('estado', 'aprobado_por', 'fecha_resolucion')}),
    )
