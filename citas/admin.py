from django.contrib import admin
 
from .models import Cita
 
 
@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = ("creada", "dueno", "mascota", "servicio", "fecha_iso", "hora", "telefono", "confirmada")
    list_filter = ("confirmada", "fecha_iso", "servicio", "especie")
    search_fields = ("dueno", "mascota", "telefono")
 