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
    estimado_rapido,
    gasto_eliminar,
    gasto_guardar,
    orden_eliminar,
    orden_guardar,
    orden_resolver,
    presupuesto_cierre,
    presupuesto_excel,
    presupuesto_pdf,
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
    # Control de obra (Fase 4)
    path('presupuestos/<int:pk>/gastos/nuevo/', gasto_guardar, name='gasto_crear'),
    path('presupuestos/<int:pk>/gastos/<int:gasto_pk>/', gasto_guardar, name='gasto_editar'),
    path('presupuestos/<int:pk>/gastos/<int:gasto_pk>/eliminar/', gasto_eliminar, name='gasto_eliminar'),
    path('presupuestos/<int:pk>/ordenes/nueva/', orden_guardar, name='orden_crear'),
    path('presupuestos/<int:pk>/ordenes/<int:orden_pk>/', orden_guardar, name='orden_editar'),
    path('presupuestos/<int:pk>/ordenes/<int:orden_pk>/eliminar/', orden_eliminar, name='orden_eliminar'),
    path('presupuestos/<int:pk>/ordenes/<int:orden_pk>/<str:decision>/', orden_resolver, name='orden_resolver'),
    # Exportación (Fase 5)
    path('presupuestos/<int:pk>/pdf/', presupuesto_pdf, name='presupuesto_pdf'),
    path('presupuestos/<int:pk>/excel/', presupuesto_excel, name='presupuesto_excel'),
    path('presupuestos/<int:pk>/cierre/', presupuesto_cierre, name='presupuesto_cierre'),
    path('catalogo/buscar/', catalogo_buscar, name='catalogo_buscar'),
    path('propiedades/<int:propiedad_pk>/estimado-rapido/', estimado_rapido, name='estimado_rapido'),
]