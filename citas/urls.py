from django.urls import path
from . import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("notificar_cita/", views.notificar_cita, name="notificar_cita"),
]