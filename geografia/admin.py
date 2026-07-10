from django.contrib import admin

from geografia.models import Estado, Municipio, ZonaMercado


@admin.register(Estado)
class EstadoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'clave']
    search_fields = ['nombre', 'clave']


@admin.register(Municipio)
class MunicipioAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'estado']
    list_filter = ['estado']
    search_fields = ['nombre']


@admin.register(ZonaMercado)
class ZonaMercadoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'colonia', 'municipio', 'radio_metros', 'activa']
    list_filter = ['municipio__estado', 'activa']
    search_fields = ['nombre', 'colonia', 'ciudad']