import uuid

from django.db import models


def generar_token():
    """Código único que viaja en el enlace de Telegram para ligar al cliente con su cita."""
    return uuid.uuid4().hex


class Cita(models.Model):
    mascota = models.CharField(max_length=100)
    especie = models.CharField(max_length=50)
    servicio = models.CharField(max_length=100)
    fecha = models.CharField(max_length=50)
    fecha_iso = models.DateField(null=True, blank=True)  # fecha real, para revisar horas ocupadas
    hora = models.CharField(max_length=10)
    dueno = models.CharField(max_length=100)
    telefono = models.CharField(max_length=30)

    # Para avisarle al cliente por Telegram cuando se confirme
    token = models.CharField(max_length=32, unique=True, default=generar_token, editable=False)
    cliente_chat_id = models.BigIntegerField(null=True, blank=True)
    confirmada = models.BooleanField(default=False)

    creada = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.mascota} - {self.dueno} ({self.fecha} {self.hora})"