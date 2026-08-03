from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
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
# Las vistas del módulo viven en su propia app (Django idiomático), pero las rutas
# se declaran aquí junto a las demás, que es la convención de este proyecto.
from presupuestos.views import (
    PresupuestoListView,
    catalogo_buscar,
    partida_eliminar,
    partida_guardar,
    presupuesto_crear,
    presupuesto_detalle,
)

admin.site.site_header = 'Casa Verde — Administración'
admin.site.site_title = 'Casa Verde'
admin.site.index_title = 'Panel de oportunidades inmobiliarias'

urlpatterns = [
    path('admin/', admin.site.urls),
    path(
        'login/',
        LoginView.as_view(template_name='registration/login.html', redirect_authenticated_user=True),
        name='login',
    ),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('', dashboard, name='dashboard'),
    path('propiedades/', PropiedadListView.as_view(), name='propiedades_lista'),
    path('propiedades/exportar/', exportar_propiedades_csv, name='exportar_csv'),
    path('propiedades/<int:pk>/', propiedad_detalle, name='propiedad_detalle'),
    path('alertas/', alertas_lista, name='alertas_lista'),
    path('alertas/configuracion/', alertas_configuracion, name='alertas_configuracion'),
    path('alertas/<int:pk>/leida/', alerta_marcar_leida, name='alerta_leida'),
    path('busqueda/', busqueda_config, name='busqueda_config'),
    path('busqueda/<int:pk>/ejecutar/', busqueda_ejecutar, name='busqueda_ejecutar'),
    path('presupuestos/', PresupuestoListView.as_view(), name='presupuestos_lista'),
    path('presupuestos/nuevo/', presupuesto_crear, name='presupuesto_crear'),
    path('presupuestos/<int:pk>/', presupuesto_detalle, name='presupuesto_detalle'),
    path('presupuestos/<int:pk>/partidas/nueva/', partida_guardar, name='partida_crear'),
    path('presupuestos/<int:pk>/partidas/<int:partida_pk>/', partida_guardar, name='partida_editar'),
    path('presupuestos/<int:pk>/partidas/<int:partida_pk>/eliminar/', partida_eliminar, name='partida_eliminar'),
    path('catalogo/buscar/', catalogo_buscar, name='catalogo_buscar'),
]