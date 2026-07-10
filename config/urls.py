from django.contrib import admin
from django.urls import path

from core.views import (
    PropiedadListView,
    alerta_marcar_leida,
    alertas_configuracion,
    alertas_lista,
    busqueda_config,
    busqueda_ejecutar,
    dashboard,
    exportar_propiedades_csv,
    propiedad_detalle,
)

admin.site.site_header = 'Casa Verde — Administración'
admin.site.site_title = 'Casa Verde'
admin.site.index_title = 'Panel de oportunidades inmobiliarias'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard, name='dashboard'),
    path('propiedades/', PropiedadListView.as_view(), name='propiedades_lista'),
    path('propiedades/exportar/', exportar_propiedades_csv, name='exportar_csv'),
    path('propiedades/<int:pk>/', propiedad_detalle, name='propiedad_detalle'),
    path('alertas/', alertas_lista, name='alertas_lista'),
    path('alertas/configuracion/', alertas_configuracion, name='alertas_configuracion'),
    path('alertas/<int:pk>/leida/', alerta_marcar_leida, name='alerta_leida'),
    path('busqueda/', busqueda_config, name='busqueda_config'),
    path('busqueda/<int:pk>/ejecutar/', busqueda_ejecutar, name='busqueda_ejecutar'),
]