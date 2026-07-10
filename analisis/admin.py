from django.contrib import admin

from analisis.models import AnalisisInversion, ConfiguracionBusqueda


@admin.register(AnalisisInversion)
class AnalisisInversionAdmin(admin.ModelAdmin):
    list_display = [
        'propiedad', 'valor_total_estimado', 'descuento_mercado',
        'roi', 'roi_anualizado', 'semaforo', 'es_oportunidad', 'es_prioritaria',
    ]
    list_filter = ['semaforo', 'es_oportunidad', 'es_prioritaria', 'datos_completos']
    search_fields = ['propiedad__titulo']
    readonly_fields = [
        'valor_terreno_estimado', 'valor_construccion_estimado', 'valor_total_estimado',
        'inversion_total', 'utilidad_potencial', 'descuento_mercado',
        'roi', 'roi_anualizado', 'anos_recuperacion', 'semaforo',
        'es_oportunidad', 'es_prioritaria', 'recomendacion', 'calculado_en',
    ]


@admin.register(ConfiguracionBusqueda)
class ConfiguracionBusquedaAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'zona', 'tipo_inmueble', 'frecuencia', 'activa', 'ultima_ejecucion']
    list_filter = ['activa', 'frecuencia', 'tipo_inmueble']