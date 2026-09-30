import hmac
import json
from datetime import datetime

import requests
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Cita


# ---------- Páginas ----------

def inicio(request):
    return render(request, 'index.html')


def cuidados(request):
    return render(request, 'cuidadomasc.html')


def doctores(request):
    return render(request, 'doctores.html')


def productos(request):
    return render(request, 'productosmasc.html')


def contacto(request):
    return render(request, 'contactoyserv.html')


# ---------- Telegram ----------

def telegram(metodo, **payload):
    """Llama a un método de la API de Telegram."""
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/{metodo}"
    r = requests.post(url, json=payload, timeout=10)
    r.raise_for_status()
    return r.json()


def mensaje_confirmacion(cita):
    return (
        "✅ ¡Tu cita ha sido confirmada!\n\n"
        f"Mascota: {cita.mascota}\n"
        f"Servicio: {cita.servicio}\n"
        f"Fecha: {cita.fecha}\n"
        f"Hora: {cita.hora}\n\n"
        "Te esperamos en Patitas Felices 🐾"
    )


# ---------- Horario de atención ----------
# Días: 0 = domingo, 1 = lunes ... 6 = sábado. None = cerrado.
# Debe coincidir con HORARIOS del index.html.
HORARIOS = {
    0: None,
    1: ("09:00", "18:00"),
    2: ("09:00", "18:00"),
    3: ("09:00", "18:00"),
    4: ("09:00", "18:00"),
    5: ("09:00", "18:00"),
    6: ("09:00", "14:00"),
}
INTERVALO_MIN = 30  # duración de cada cita en minutos


def a_minutos(hhmm):
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def validar_horario(fecha_iso, hora):
    """Devuelve un texto de error si la fecha/hora no es válida, o None si todo está bien."""
    try:
        fecha = datetime.strptime(fecha_iso, "%Y-%m-%d").date()
        minutos = a_minutos(hora)
    except (ValueError, TypeError, AttributeError):
        return "Fecha u hora inválidas"

    rango = HORARIOS.get(fecha.isoweekday() % 7)
    if not rango:
        return "Ese día no hay atención"

    inicio, fin = a_minutos(rango[0]), a_minutos(rango[1])
    if minutos < inicio or minutos + INTERVALO_MIN > fin or (minutos - inicio) % INTERVALO_MIN != 0:
        return "Esa hora está fuera del horario de atención"

    ahora = timezone.localtime()
    if fecha < ahora.date() or (fecha == ahora.date() and minutos <= ahora.hour * 60 + ahora.minute):
        return "Esa hora ya pasó"

    return None


@require_POST
def notificar_cita(request):
    try:
        datos = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)

    campos = ["mascota", "especie", "servicio", "fecha", "hora", "dueno", "telefono"]
    if not all(datos.get(c) for c in campos):
        return JsonResponse({"ok": False, "error": "Faltan datos"}, status=400)

    error = validar_horario(datos.get("fecha_iso"), datos.get("hora"))
    if error:
        return JsonResponse({"ok": False, "error": error}, status=400)

    # Se guarda primero, para que no se pierda si Telegram falla
    cita = Cita.objects.create(**{c: datos[c] for c in campos})

    texto = (
        f"🐾 Nueva cita #{cita.id}\n\n"
        f"Dueño: {cita.dueno}\n"
        f"Mascota: {cita.mascota} ({cita.especie})\n"
        f"Servicio: {cita.servicio}\n"
        f"Fecha: {cita.fecha}\n"
        f"Hora: {cita.hora}\n"
        f"Teléfono: {cita.telefono}"
    )

    try:
        telegram(
            "sendMessage",
            chat_id=settings.TELEGRAM_CHAT_ID,
            text=texto,
            reply_markup={
                "inline_keyboard": [[
                    {"text": "✅ Confirmar cita", "callback_data": f"confirmar:{cita.id}"}
                ]]
            },
        )
    except requests.RequestException:
        return JsonResponse({"ok": False, "error": "No se pudo enviar"}, status=502)

    # Enlace para que el cliente abra el bot y reciba ahí su confirmación
    enlace = ""
    if settings.TELEGRAM_BOT_USERNAME:
        enlace = f"https://t.me/{settings.TELEGRAM_BOT_USERNAME}?start={cita.token}"

    return JsonResponse({"ok": True, "enlace": enlace})


@csrf_exempt
@require_POST
def telegram_webhook(request):
    """Telegram avisa aquí cuando alguien le escribe al bot o toca un botón."""
    esperado = settings.TELEGRAM_WEBHOOK_SECRET
    recibido = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if not esperado or not hmac.compare_digest(recibido, esperado):
        return HttpResponse(status=403)

    try:
        update = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse(status=400)

    try:
        if "message" in update:
            procesar_mensaje(update["message"])
        elif "callback_query" in update:
            procesar_boton(update["callback_query"])
    except requests.RequestException:
        pass  # Siempre respondemos 200 para que Telegram no reintente sin parar

    return HttpResponse("ok")


def procesar_mensaje(msg):
    """El cliente abrió el bot desde el enlace de su cita (/start <token>)."""
    chat_id = msg["chat"]["id"]
    texto = msg.get("text", "")
    if not texto.startswith("/start"):
        return

    partes = texto.split(maxsplit=1)
    if len(partes) < 2:
        telegram(
            "sendMessage",
            chat_id=chat_id,
            text="¡Hola! Soy el asistente de Patitas Felices 🐾\n"
                 "Agenda tu cita en nuestro sitio web para recibir aquí tu confirmación.",
        )
        return

    cita = Cita.objects.filter(token=partes[1].strip()).first()
    if not cita:
        telegram("sendMessage", chat_id=chat_id,
                 text="No encontré esa cita. Intenta agendarla de nuevo desde nuestro sitio.")
        return

    cita.cliente_chat_id = chat_id
    cita.save(update_fields=["cliente_chat_id"])

    if cita.confirmada:
        telegram("sendMessage", chat_id=chat_id, text=mensaje_confirmacion(cita))
    else:
        telegram(
            "sendMessage",
            chat_id=chat_id,
            text=f"¡Gracias, {cita.dueno}! Recibimos tu solicitud de cita para {cita.mascota}.\n"
                 "En cuanto la confirmemos te avisaremos por este chat 🐾",
        )


def procesar_boton(cb):
    """La veterinaria tocó el botón 'Confirmar cita'."""
    mensaje = cb.get("message") or {}
    chat_id = (mensaje.get("chat") or {}).get("id")

    # Solo el chat de la veterinaria puede confirmar
    if str(chat_id) != str(settings.TELEGRAM_CHAT_ID):
        telegram("answerCallbackQuery", callback_query_id=cb["id"], text="No autorizado")
        return

    data = cb.get("data", "")
    if not data.startswith("confirmar:"):
        return
    cita_id = data.split(":", 1)[1]
    if not cita_id.isdigit():
        return

    cita = Cita.objects.filter(pk=int(cita_id)).first()
    if not cita:
        telegram("answerCallbackQuery", callback_query_id=cb["id"], text="No encontré esa cita")
        return

    if cita.confirmada:
        telegram("answerCallbackQuery", callback_query_id=cb["id"], text="Esta cita ya estaba confirmada")
        return

    cita.confirmada = True
    cita.save(update_fields=["confirmada"])

    if cita.cliente_chat_id:
        telegram("sendMessage", chat_id=cita.cliente_chat_id, text=mensaje_confirmacion(cita))
        aviso = "✅ Cita confirmada y cliente notificado"
    else:
        aviso = (f"✅ Cita confirmada, pero el cliente aún no abrió el bot. "
                 f"Avísale al {cita.telefono}")

    telegram("answerCallbackQuery", callback_query_id=cb["id"], text=aviso, show_alert=True)

    # Quita el botón para que no se pulse dos veces
    if mensaje.get("message_id"):
        telegram(
            "editMessageReplyMarkup",
            chat_id=chat_id,
            message_id=mensaje["message_id"],
            reply_markup={"inline_keyboard": []},
        )