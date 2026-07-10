from django.contrib import admin

from alertas.models import Alerta


@admin.register(Alerta)
class AlertaAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'tipo', 'canal', 'enviada', 'leida', 'creada_en']
    list_filter = ['tipo', 'canal', 'enviada', 'leida']
    search_fields = ['mensaje', 'usuario__username']