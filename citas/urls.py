from django.urls import path
from . import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("notificar_cita/", views.notificar_cita, name="notificar_cita"),
    path("cuidados/", views.cuidados, name="cuidados"),
    path("doctores/", views.doctores, name="doctores"),
    path("productos/", views.productos, name="productos"),
    path("contacto/", views.contacto, name="contacto"),
]