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

from presupuestos.models import OrdenCambio, PartidaPresupuesto, Presupuesto


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
    """
    if presupuesto.es_activo:
        analizar(presupuesto.propiedad)


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
        analizar(instance.propiedad)


@receiver(post_save, sender=PartidaPresupuesto)
@receiver(post_delete, sender=PartidaPresupuesto)
def partida_cambiada(sender, instance, **kwargs):
    """Una partida cambia el total, y el total es lo que alimenta el ROI."""
    recalcular_roi(instance.presupuesto)


# OrdenCambio se importa aquí a propósito aunque todavía no dispare nada: en
# Fase 4, cuando una orden aprobada modifique el alcance, este es el lugar donde
# enganchar su recálculo. Dejarlo señalado evita que se resuelva por otro lado.
__all__ = ['recalcular_roi', 'OrdenCambio']
