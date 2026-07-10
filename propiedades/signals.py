from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from propiedades.models import HistorialPrecio, Propiedad
from services.oportunidad import OportunidadService


@receiver(pre_save, sender=Propiedad)
def registrar_cambio_precio(sender, instance, **kwargs):
    if instance.pk:
        anterior = Propiedad.objects.filter(pk=instance.pk).first()
        if anterior and anterior.precio_publicado != instance.precio_publicado:
            HistorialPrecio.objects.create(
                propiedad=instance,
                precio_anterior=anterior.precio_publicado,
                precio_nuevo=instance.precio_publicado,
                motivo='Actualización automática',
            )
            if instance.precio_publicado < anterior.precio_publicado:
                from services.alerta import AlertaService
                AlertaService.notificar_baja_precio(instance, anterior.precio_publicado)


@receiver(post_save, sender=Propiedad)
def analizar_propiedad_automaticamente(sender, instance, created, **kwargs):
    update_fields = kwargs.get('update_fields')
    if update_fields and set(update_fields).issubset({'semaforo', 'estatus', 'actualizado_en'}):
        return
    if instance.precio_publicado and instance.zona_id:
        OportunidadService.analizar_propiedad(instance, usuario=instance.capturado_por)