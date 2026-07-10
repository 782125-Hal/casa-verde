from django.contrib import admin

from propiedades.models import HistorialPrecio, Propiedad


class HistorialPrecioInline(admin.TabularInline):
    model = HistorialPrecio
    extra = 0
    readonly_fields = ['precio_anterior', 'precio_nuevo', 'fecha_cambio', 'motivo']


@admin.register(Propiedad)
class PropiedadAdmin(admin.ModelAdmin):
    list_display = [
        'titulo', 'tipo_inmueble', 'precio_publicado', 'zona',
        'semaforo', 'estatus', 'fecha_deteccion',
    ]
    list_filter = ['tipo_inmueble', 'semaforo', 'estatus', 'zona__municipio__estado']
    search_fields = ['titulo', 'descripcion', 'direccion']
    readonly_fields = ['semaforo', 'fecha_deteccion', 'actualizado_en']
    inlines = [HistorialPrecioInline]
    fieldsets = (
        ('Información general', {
            'fields': ('titulo', 'descripcion', 'tipo_inmueble', 'estatus', 'semaforo'),
        }),
        ('Ubicación', {
            'fields': ('zona', 'direccion', 'latitud', 'longitud'),
        }),
        ('Precio y superficie', {
            'fields': ('precio_publicado', 'm2_terreno', 'm2_construccion'),
        }),
        ('Características', {
            'fields': (
                'habitaciones', 'banos', 'niveles', 'estacionamientos',
                'antiguedad_anos', 'estado_fisico', 'nivel_remodelacion',
            ),
        }),
        ('Riesgos', {
            'fields': ('riesgo_documental', 'riesgo_legal', 'riesgo_fisico'),
        }),
        ('Fuente y contacto', {
            'fields': ('fuente', 'url_anuncio', 'imagen_url', 'contacto_publico', 'fecha_publicacion'),
        }),
        ('Metadatos', {
            'fields': ('capturado_por', 'fecha_deteccion', 'actualizado_en'),
        }),
    )


@admin.register(HistorialPrecio)
class HistorialPrecioAdmin(admin.ModelAdmin):
    list_display = ['propiedad', 'precio_anterior', 'precio_nuevo', 'fecha_cambio']
    list_filter = ['fecha_cambio']