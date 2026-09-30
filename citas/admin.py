from django.contrib import admin

from .models import Cita


@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = ("creada", "dueno", "mascota", "servicio", "fecha", "hora", "telefono", "confirmada")
    list_filter = ("confirmada", "servicio", "especie")
    search_fields = ("dueno", "mascota", "telefono")