"""Vistas de la pestaña Presupuestos (Fase 2).

Convenciones del proyecto: ``@login_required`` en las funciones y
``LoginRequiredMixin`` en las CBV; templates en ``templates/presupuestos/``; las
rutas se declaran en ``config/urls.py`` junto a las demás.

Permisos: cualquier usuario autenticado (§6.3 quedó sin decidir, así que no se
inventan roles granulares).

Fuera de alcance por ahora: el ROI (Fase 3), los gastos reales y las órdenes de
cambio (Fase 4) y la exportación (Fase 5).
"""
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView

from presupuestos.choices import (
    CATEGORIA_CHOICES,
    ESTADO_PRESUPUESTO_CHOICES,
    TIPO_OBRA_CHOICES,
)
from presupuestos.forms import PartidaForm, PresupuestoCrearForm, PresupuestoForm
from presupuestos.models import CatalogoConcepto, PartidaPresupuesto, Presupuesto
from presupuestos.plantillas import aplicar_plantilla

_ETIQUETA_CATEGORIA = dict(CATEGORIA_CHOICES)


class PresupuestoListView(LoginRequiredMixin, ListView):
    """Lista con filtros por estado y tipo de obra."""

    model = Presupuesto
    template_name = 'presupuestos/lista.html'
    context_object_name = 'presupuestos'
    paginate_by = 20

    def get_queryset(self):
        qs = Presupuesto.objects.select_related('propiedad', 'propiedad__zona')
        # Los totales son propiedades calculadas y cada una consulta las partidas;
        # sin prefetch la lista haría N consultas por página.
        qs = qs.prefetch_related('partidas', 'gastos')
        estado = self.request.GET.get('estado')
        tipo = self.request.GET.get('tipo_obra')
        propiedad = self.request.GET.get('propiedad')
        if estado:
            qs = qs.filter(estado=estado)
        if tipo:
            qs = qs.filter(tipo_obra=tipo)
        if propiedad:
            qs = qs.filter(propiedad_id=propiedad)
        return qs.order_by('-creado_en')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['estados'] = ESTADO_PRESUPUESTO_CHOICES
        ctx['tipos_obra'] = TIPO_OBRA_CHOICES
        ctx['estado_actual'] = self.request.GET.get('estado', '')
        ctx['tipo_actual'] = self.request.GET.get('tipo_obra', '')
        return ctx


def _partidas_por_categoria(presupuesto):
    """Partidas agrupadas por categoría, con el subtotal de cada grupo.

    Se agrupa en Python y no con ``regroup`` en el template porque hace falta el
    subtotal por categoría, que la plantilla no puede sumar sola.
    """
    grupos = {}
    for partida in presupuesto.partidas.all():
        grupo = grupos.setdefault(partida.categoria, {
            'categoria': partida.categoria,
            'etiqueta': _ETIQUETA_CATEGORIA.get(partida.categoria, partida.categoria),
            'partidas': [],
            'subtotal': Decimal('0.00'),
        })
        grupo['partidas'].append(partida)
        grupo['subtotal'] += partida.importe
    return sorted(grupos.values(), key=lambda g: g['etiqueta'])


@login_required
def presupuesto_detalle(request, pk):
    """Detalle y captura: encabezado editable, partidas y desglose en vivo."""
    presupuesto = get_object_or_404(
        Presupuesto.objects.select_related('propiedad'), pk=pk,
    )

    if request.method == 'POST':
        form = PresupuestoForm(request.POST, instance=presupuesto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Presupuesto actualizado.')
            return redirect('presupuesto_detalle', pk=presupuesto.pk)
        messages.error(request, 'Revisa los datos del encabezado.')
    else:
        form = PresupuestoForm(instance=presupuesto)

    return render(request, 'presupuestos/detalle.html', {
        'presupuesto': presupuesto,
        'form': form,
        'grupos': _partidas_por_categoria(presupuesto),
        'partida_form': PartidaForm(),
        'categorias': CATEGORIA_CHOICES,
    })


@login_required
def presupuesto_crear(request):
    """Alta. Si se eligió plantilla, precarga sus partidas con cantidad 0."""
    if request.method == 'POST':
        form = PresupuestoCrearForm(request.POST)
        if form.is_valid():
            presupuesto = form.save(commit=False)
            presupuesto.creado_por = request.user
            presupuesto.save()

            clave = form.cleaned_data.get('plantilla')
            if clave:
                creadas, faltantes = aplicar_plantilla(presupuesto, clave)
                messages.success(
                    request, f'Presupuesto creado con {creadas} partida(s) de la plantilla. '
                             'Ajusta las cantidades.',
                )
                if faltantes:
                    # Sin esto el usuario vería menos renglones y no sabría por qué.
                    messages.warning(
                        request,
                        f'{len(faltantes)} concepto(s) de la plantilla no están en el '
                        f'catálogo y se omitieron ({", ".join(faltantes[:5])}'
                        f'{"…" if len(faltantes) > 5 else ""}). '
                        'Corre: python manage.py seed_catalogo',
                    )
            else:
                messages.success(request, 'Presupuesto creado. Agrega sus partidas.')
            return redirect('presupuesto_detalle', pk=presupuesto.pk)
        messages.error(request, 'Revisa los datos del formulario.')
    else:
        form = PresupuestoCrearForm()

    return render(request, 'presupuestos/form.html', {'form': form})


@login_required
def partida_guardar(request, pk, partida_pk=None):
    """Alta y edición de una partida. Siempre POST desde el detalle."""
    presupuesto = get_object_or_404(Presupuesto, pk=pk)
    if request.method != 'POST':
        return redirect('presupuesto_detalle', pk=presupuesto.pk)

    instancia = None
    if partida_pk:
        instancia = get_object_or_404(
            PartidaPresupuesto, pk=partida_pk, presupuesto=presupuesto,
        )

    form = PartidaForm(request.POST, instance=instancia)
    if form.is_valid():
        partida = form.save(commit=False)
        partida.presupuesto = presupuesto
        partida.save()
        messages.success(
            request, 'Partida actualizada.' if partida_pk else 'Partida agregada.',
        )
    else:
        errores = '; '.join(
            f'{campo}: {", ".join(msgs)}' for campo, msgs in form.errors.items()
        )
        messages.error(request, f'No se pudo guardar la partida — {errores}')
    return redirect('presupuesto_detalle', pk=presupuesto.pk)


@login_required
def partida_eliminar(request, pk, partida_pk):
    presupuesto = get_object_or_404(Presupuesto, pk=pk)
    if request.method != 'POST':
        return redirect('presupuesto_detalle', pk=presupuesto.pk)
    partida = get_object_or_404(
        PartidaPresupuesto, pk=partida_pk, presupuesto=presupuesto,
    )
    partida.delete()
    messages.success(request, 'Partida eliminada.')
    return redirect('presupuesto_detalle', pk=presupuesto.pk)


@login_required
def catalogo_buscar(request):
    """Autocompletado del catálogo para la captura de partidas.

    Devuelve el PU ya sumado para que el front no tenga que recomponerlo; el
    template copia estos valores al renglón y los deja editables.
    """
    termino = (request.GET.get('q') or '').strip()
    qs = CatalogoConcepto.objects.filter(activo=True)
    if termino:
        qs = qs.filter(descripcion__icontains=termino) | qs.filter(codigo__icontains=termino)
    categoria = request.GET.get('categoria')
    if categoria:
        qs = qs.filter(categoria=categoria)

    resultados = [
        {
            'id': c.pk,
            'codigo': c.codigo,
            'descripcion': c.descripcion,
            'categoria': c.categoria,
            'unidad': c.unidad,
            'pu': str(c.pu_total),
        }
        for c in qs.order_by('categoria', 'codigo')[:20]
    ]
    return JsonResponse({'resultados': resultados})
