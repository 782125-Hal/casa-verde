from django.contrib import admin

from mercado.models import (
    ComparativoMercado,
    CostoRemodelacionM2,
    FuenteDatos,
    ScrapeEjecucion,
    TasaReferenciaBancaria,
    ValorMetroCuadrado,
)


@admin.register(FuenteDatos)
class FuenteDatosAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo', 'activa', 'requiere_api']
    list_filter = ['tipo', 'activa']


@admin.register(ValorMetroCuadrado)
class ValorMetroCuadradoAdmin(admin.ModelAdmin):
    list_display = [
        'zona', 'tipo_inmueble', 'valor_terreno_m2', 'valor_construccion_m2',
        'fecha_actualizacion', 'confiabilidad',
    ]
    list_filter = ['tipo_inmueble', 'zona__municipio__estado', 'confiabilidad']
    search_fields = ['zona__nombre']
    date_hierarchy = 'fecha_actualizacion'


@admin.register(TasaReferenciaBancaria)
class TasaReferenciaBancariaAdmin(admin.ModelAdmin):
    list_display = ['institucion', 'tasa_anual', 'fecha_vigencia', 'es_default', 'fuente']
    list_filter = ['es_default']


@admin.register(ScrapeEjecucion)
class ScrapeEjecucionAdmin(admin.ModelAdmin):
    list_display = ['fuente', 'zona', 'estado', 'encontrados', 'nuevos', 'actualizados', 'errores', 'iniciado_en']
    list_filter = ['estado', 'fuente', 'zona']
    readonly_fields = ['log', 'iniciado_en', 'finalizado_en']


@admin.register(ComparativoMercado)
class ComparativoMercadoAdmin(admin.ModelAdmin):
    list_display = ['zona', 'tipo_inmueble', 'precio_promedio_m2', 'total_propiedades', 'periodo']
    list_filter = ['tipo_inmueble']


@admin.register(CostoRemodelacionM2)
class CostoRemodelacionM2Admin(admin.ModelAdmin):
    list_display = ['zona', 'nivel_obra', 'costo_m2', 'fecha_actualizacion', 'confiabilidad']
    list_filter = ['nivel_obra', 'zona__municipio__estado', 'confiabilidad']
    search_fields = ['zona__nombre']
    date_hierarchy = 'fecha_actualizacion'