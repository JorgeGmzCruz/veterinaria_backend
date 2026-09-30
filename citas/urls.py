from django.urls import path

from . import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("cuidados/", views.cuidados, name="cuidados"),
    path("doctores/", views.doctores, name="doctores"),
    path("productos/", views.productos, name="productos"),
    path("contacto/", views.contacto, name="contacto"),
    path("notificar_cita/", views.notificar_cita, name="notificar_cita"),
    path("telegram/webhook/", views.telegram_webhook, name="telegram_webhook"),
]