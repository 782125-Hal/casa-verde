"""Recálculo del ROI cuando cambia un presupuesto activo (Fase 3).

El flujo del §3.1 del diseño:

    Presupuesto activo → total → costo de remodelación → ROI y semáforo

No se recalcula nada a mano: se reusa ``OportunidadService.analizar_propiedad``,
el mismo que corre cuando se captura una propiedad. Aquí solo se decide CUÁNDO
volver a llamarlo.

Sobre bucles infinitos: ``analizar_propiedad`` termina guardando la propiedad con
``update_fields=['semaforo', 'estatus']``, y el ``post_save`` de ``Propiedad``
sale temprano ante ese conjunto de campos. La cadena se corta ahí.
"""
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from presupuestos.models import (
    OrdenCambio,
    PartidaPresupuesto,
    Presupuesto,
    RegistroGasto,
)


def _relacion_viva(instancia, campo):
    """Devuelve la relación, o None si ya desapareció.

    Hace falta en los ``post_delete``: al borrar un presupuesto, Django cascadea
    partidas y gastos, y cuando la señal del hijo se ejecuta el padre puede haber
    desaparecido ya. Sin esta guarda, acceder a la FK lanza ``DoesNotExist`` y
    revienta el borrado entero.
    """
    from django.core.exceptions import ObjectDoesNotExist

    try:
        return getattr(instancia, campo)
    except ObjectDoesNotExist:
        return None


def analizar(propiedad):
    """Reanaliza la propiedad. No decide nada: solo comprueba que se pueda."""
    if propiedad is None:
        return
    if not (propiedad.precio_publicado and propiedad.zona_id):
        return  # analizar_propiedad exige ambos; el post_save de Propiedad igual

    from services.oportunidad import OportunidadService

    OportunidadService.analizar_propiedad(propiedad, usuario=propiedad.capturado_por)


def recalcular_roi(presupuesto):
    """Reanaliza si ESTE presupuesto es el que manda sobre el ROI.

    Un escenario alternativo ("premium") no debe mover el semáforo mientras no se
    marque activo, así que los inactivos no disparan nada.

    La FK se lee con guarda: esto corre también desde ``post_delete`` de partidas
    y órdenes, y si lo que se está borrando es la PROPIEDAD, la cascada ya se la
    llevó cuando llega la señal del nieto.
    """
    if presupuesto.es_activo:
        analizar(_relacion_viva(presupuesto, 'propiedad'))


@receiver(pre_save, sender=Presupuesto)
def recordar_si_estaba_activo(sender, instance, **kwargs):
    """Guarda el ``es_activo`` que había en la BD antes de este save.

    Hace falta para el caso que se escapa a la vista simple: al DESACTIVAR un
    presupuesto hay que recalcular precisamente porque deja de mandar, y mirando
    solo el valor nuevo (False) se saltaría el recálculo y la propiedad se
    quedaría con el costo del presupuesto que ya no está activo.
    """
    if not instance.pk:
        instance._estaba_activo = False
        return
    anterior = Presupuesto.objects.filter(pk=instance.pk).values_list(
        'es_activo', flat=True,
    ).first()
    instance._estaba_activo = bool(anterior)


@receiver(post_save, sender=Presupuesto)
def presupuesto_guardado(sender, instance, **kwargs):
    """Cambió el encabezado: %, área, tipo de obra o el propio ``es_activo``."""
    if instance.es_activo or getattr(instance, '_estaba_activo', False):
        analizar(instance.propiedad)


@receiver(post_delete, sender=Presupuesto)
def presupuesto_borrado(sender, instance, **kwargs):
    """Al borrar el activo, la propiedad vuelve al estimado paramétrico.

    Se llama a ``analizar`` directamente y no a ``recalcular_roi``: la fila ya no
    está en la BD, así que ``estimar()`` no la encontrará y devolverá el
    paramétrico, que es justo lo que se quiere persistir.
    """
    if instance.es_activo:
        # También aquí: si lo que se está borrando es la PROPIEDAD, la cascada ya
        # se la llevó y no hay nada que reanalizar.
        analizar(_relacion_viva(instance, 'propiedad'))


@receiver(post_save, sender=PartidaPresupuesto)
@receiver(post_delete, sender=PartidaPresupuesto)
def partida_cambiada(sender, instance, **kwargs):
    """Una partida cambia el total, y el total es lo que alimenta el ROI."""
    presupuesto = _relacion_viva(instance, 'presupuesto')
    if presupuesto is not None:
        recalcular_roi(presupuesto)


def revisar_salud(presupuesto):
    """Evalúa el control de obra y avisa si hace falta (§4.4).

    El servicio decide si corresponde alertar y deduplica; aquí solo se elige
    CUÁNDO revisar: cada vez que cambia el gasto real o una orden de cambio.
    """
    from services.alerta import AlertaService

    AlertaService.notificar_presupuesto(presupuesto)


@receiver(post_save, sender=RegistroGasto)
@receiver(post_delete, sender=RegistroGasto)
def gasto_registrado(sender, instance, **kwargs):
    """El gasto real es lo que mueve el semáforo de desviación.

    No toca el ROI: lo presupuestado no cambia porque se gaste más. El §4.6 sí
    contempla un "ROI proyectado con costos reales", pero eso es un indicador
    aparte, no una reescritura del análisis de la propiedad.
    """
    presupuesto = _relacion_viva(instance, 'presupuesto')
    if presupuesto is None:
        return
    revisar_salud(presupuesto)
    if instance.partida_id:
        from services.alerta import AlertaService

        partida = _relacion_viva(instance, 'partida')
        if partida is not None:
            AlertaService.notificar_partida_desviada(partida)


@receiver(post_save, sender=OrdenCambio)
@receiver(post_delete, sender=OrdenCambio)
def orden_cambio_guardada(sender, instance, **kwargs):
    """Una orden APROBADA mueve los techos: con capital adicional sube el
    presupuesto aprobado, y con cargo a contingencia consume reserva.

    Como el techo con capital adicional también cambia el costo del ROI, se
    recalcula el análisis además de revisar la salud.
    """
    presupuesto = _relacion_viva(instance, 'presupuesto')
    if presupuesto is None:
        return
    recalcular_roi(presupuesto)
    revisar_salud(presupuesto)


__all__ = ['recalcular_roi', 'revisar_salud']
