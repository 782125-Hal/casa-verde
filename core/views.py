import csv
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView

from alertas.models import Alerta
from analisis.forms import ConfiguracionBusquedaForm, ImportarCSVForm, ImportarURLForm
from analisis.models import AnalisisInversion, ConfiguracionBusqueda
from geografia.models import ZonaMercado
from mercado.models import ScrapeEjecucion
from propiedades.models import Propiedad
from services.alerta import AlertaService
from services.busqueda import BusquedaService
from services.scraping import ScrapingService
from services.scraping.csv_importer import CSVImporter
from services.telegram import telegram_configurado
from usuarios.forms import PreferenciasAlertaForm


def dashboard(request):
    """Panel de control con filtros y datos para gráficas."""
    zona_id = request.GET.get('zona')
    propiedades = Propiedad.objects.select_related('zona', 'analisis')
    analisis = AnalisisInversion.objects.select_related('propiedad', 'propiedad__zona')

    if zona_id:
        propiedades = propiedades.filter(zona_id=zona_id)
        analisis = analisis.filter(propiedad__zona_id=zona_id)

    total_analizadas = propiedades.count()
    oportunidades = analisis.filter(es_oportunidad=True).count()
    prioritarias = analisis.filter(es_prioritaria=True).count()
    descartadas = propiedades.filter(estatus='descartada').count()

    promedio_descuento = analisis.filter(
        datos_completos=True, descuento_mercado__gt=0,
    ).aggregate(prom=Avg('descuento_mercado'))['prom'] or 0

    por_semaforo = list(
        propiedades.values('semaforo').annotate(total=Count('id')).order_by('semaforo')
    )

    ranking = analisis.filter(
        es_oportunidad=True,
    ).select_related('propiedad', 'propiedad__zona').order_by('-descuento_mercado')[:10]

    zonas_top = (
        analisis.filter(es_oportunidad=True)
        .values('propiedad__zona__nombre')
        .annotate(total=Count('id'), desc_prom=Avg('descuento_mercado'))
        .order_by('-total')[:6]
    )

    alertas_recientes = Alerta.objects.select_related(
        'propiedad', 'propiedad__zona',
    ).order_by('-creada_en')[:5]

    zonas = ZonaMercado.objects.filter(
        activa=True, municipio__nombre='Tijuana',
    ).order_by('nombre')

    context = {
        'total_analizadas': total_analizadas,
        'oportunidades': oportunidades,
        'prioritarias': prioritarias,
        'descartadas': descartadas,
        'promedio_descuento': round(promedio_descuento, 1),
        'por_semaforo': por_semaforo,
        'por_semaforo_json': json.dumps(por_semaforo),
        'zonas_top': zonas_top,
        'zonas_top_json': json.dumps([
            {'zona': z['propiedad__zona__nombre'], 'total': z['total']} for z in zonas_top
        ]),
        'ranking': ranking,
        'ultimas': propiedades.order_by('-fecha_deteccion')[:8],
        'alertas_recientes': alertas_recientes,
        'zonas': zonas,
        'zona_actual': int(zona_id) if zona_id else None,
        'alertas_no_leidas': Alerta.objects.filter(leida=False).count(),
    }
    return render(request, 'dashboard/index.html', context)


class PropiedadListView(ListView):
    model = Propiedad
    template_name = 'propiedades/lista.html'
    context_object_name = 'propiedades'
    paginate_by = 20

    def get_queryset(self):
        qs = Propiedad.objects.select_related('zona', 'fuente').prefetch_related('analisis')
        semaforo = self.request.GET.get('semaforo')
        estatus = self.request.GET.get('estatus')
        tipo = self.request.GET.get('tipo')
        zona = self.request.GET.get('zona')
        if semaforo:
            qs = qs.filter(semaforo=semaforo)
        if estatus:
            qs = qs.filter(estatus=estatus)
        if tipo:
            qs = qs.filter(tipo_inmueble=tipo)
        if zona:
            qs = qs.filter(zona_id=zona)
        return qs.order_by('-fecha_deteccion')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['zonas'] = ZonaMercado.objects.filter(activa=True, municipio__nombre='Tijuana')
        return ctx


def propiedad_detalle(request, pk):
    propiedad = get_object_or_404(
        Propiedad.objects.select_related('zona', 'zona__municipio', 'fuente', 'analisis'),
        pk=pk,
    )
    historial = propiedad.historial_precios.all()[:10]
    similares = Propiedad.objects.filter(
        zona=propiedad.zona,
        tipo_inmueble=propiedad.tipo_inmueble,
    ).exclude(pk=pk).select_related('analisis')[:5]

    return render(request, 'propiedades/detalle.html', {
        'propiedad': propiedad,
        'analisis': getattr(propiedad, 'analisis', None),
        'historial': historial,
        'similares': similares,
    })


@login_required
def alertas_configuracion(request):
    if request.method == 'POST':
        if 'enviar_prueba' in request.POST:
            AlertaService.enviar_prueba(request.user)
            messages.success(request, 'Alerta de prueba enviada. Revisa tu email, Telegram o la app.')
            return redirect('alertas_configuracion')

        form = PreferenciasAlertaForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Preferencias de alertas guardadas.')
            return redirect('alertas_configuracion')
    else:
        form = PreferenciasAlertaForm(instance=request.user)

    return render(request, 'alertas/configuracion.html', {
        'form': form,
        'telegram_activo': telegram_configurado(),
    })


@login_required
def alertas_lista(request):
    alertas = Alerta.objects.filter(usuario=request.user).select_related(
        'propiedad', 'propiedad__zona',
    ).order_by('-creada_en')

    if request.method == 'POST':
        Alerta.objects.filter(usuario=request.user, leida=False).update(leida=True)
        messages.success(request, 'Alertas marcadas como leídas.')
        return redirect('alertas_lista')

    return render(request, 'alertas/lista.html', {
        'alertas': alertas,
        'no_leidas': alertas.filter(leida=False).count(),
    })


@login_required
def alerta_marcar_leida(request, pk):
    alerta = get_object_or_404(Alerta, pk=pk, usuario=request.user)
    alerta.leida = True
    alerta.save(update_fields=['leida'])
    return redirect('alertas_lista')


@login_required
def busqueda_config(request):
    configs = ConfiguracionBusqueda.objects.filter(
        usuario=request.user,
    ).select_related('zona').order_by('-activa', '-creada_en')

    form = ConfiguracionBusquedaForm()
    import_form = ImportarURLForm()
    csv_form = ImportarCSVForm()

    if request.method == 'POST':
        if 'importar_csv' in request.POST:
            csv_form = ImportarCSVForm(request.POST, request.FILES)
            if csv_form.is_valid():
                zonas = {
                    z.nombre.lower(): z for z in ZonaMercado.objects.filter(
                        activa=True, municipio__nombre='Tijuana',
                    )
                }
                try:
                    resultado = CSVImporter.importar(
                        csv_form.cleaned_data['archivo'], zonas, usuario=request.user,
                    )
                    messages.success(
                        request,
                        f"CSV importado: {resultado['nuevos']} nuevas, "
                        f"{resultado['actualizados']} actualizadas, {resultado['errores']} errores.",
                    )
                    return redirect('busqueda_config')
                except ValueError as exc:
                    messages.error(request, str(exc))
        elif 'importar_url' in request.POST:
            import_form = ImportarURLForm(request.POST)
            if import_form.is_valid():
                try:
                    propiedad, es_nueva = ScrapingService.importar_url(
                        import_form.cleaned_data['url'],
                        import_form.cleaned_data['zona'].pk,
                        usuario=request.user,
                    )
                    accion = 'importada' if es_nueva else 'actualizada'
                    messages.success(request, f'Propiedad {accion}: {propiedad.titulo}')
                    return redirect('propiedad_detalle', pk=propiedad.pk)
                except ValueError as exc:
                    messages.error(request, str(exc))
        else:
            form = ConfiguracionBusquedaForm(request.POST)
            if form.is_valid():
                config = form.save(commit=False)
                config.usuario = request.user
                config.save()
                messages.success(request, f'Búsqueda configurada para {config.zona.nombre}.')
                return redirect('busqueda_config')

    scrapes = ScrapeEjecucion.objects.select_related(
        'fuente', 'zona', 'configuracion',
    ).order_by('-iniciado_en')[:15]

    return render(request, 'busqueda/config.html', {
        'form': form,
        'import_form': import_form,
        'csv_form': csv_form,
        'configs': configs,
        'scrapes': scrapes,
    })


@login_required
def busqueda_ejecutar(request, pk):
    config = get_object_or_404(ConfiguracionBusqueda, pk=pk, usuario=request.user)
    resultado = BusquedaService.ejecutar_configuracion(config)
    sc = resultado.get('scrape', {})
    messages.success(
        request,
        f"Búsqueda en {resultado['zona']}: +{sc.get('nuevos', 0)} nuevas del scrape, "
        f"{resultado['propiedades_reanalizadas']} reanalizadas, "
        f"{resultado['oportunidades']} oportunidades.",
    )
    return redirect('busqueda_config')


def exportar_propiedades_csv(request):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="casa_verde_propiedades.csv"'
    response.write('\ufeff')

    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Título', 'Zona', 'Tipo', 'Precio', 'm² Terreno', 'm² Construcción',
        'Semáforo', 'Estatus', 'Descuento %', 'ROI %', 'ROI Anual %',
        'Nivel remodelación', 'Presupuesto remodelación', 'URL',
    ])

    propiedades = Propiedad.objects.select_related('zona', 'analisis').order_by('-fecha_deteccion')
    zona_id = request.GET.get('zona')
    if zona_id:
        propiedades = propiedades.filter(zona_id=zona_id)

    for p in propiedades:
        a = getattr(p, 'analisis', None)
        writer.writerow([
            p.pk, p.titulo, p.zona.nombre, p.get_tipo_inmueble_display(),
            p.precio_publicado, p.m2_terreno or '', p.m2_construccion or '',
            p.get_semaforo_display(), p.get_estatus_display(),
            a.descuento_mercado if a else '', a.roi if a else '',
            a.roi_anualizado if a else '',
            a.get_nivel_remodelacion_aplicado_display() if a and a.nivel_remodelacion_aplicado else '',
            a.presupuesto_remodelacion if a else '',
            p.url_anuncio,
        ])

    return response