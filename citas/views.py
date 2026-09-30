from django.shortcuts import render
import json
import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie

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

@ensure_csrf_cookie
def inicio(request):
    return render(request, 'index.html')

@require_POST
def notificar_cita(request):
    try:
        datos = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)

    campos = ["mascota", "especie", "servicio", "fecha", "hora", "dueno", "telefono"]
    if not all(datos.get(c) for c in campos):
        return JsonResponse({"ok": False, "error": "Faltan datos"}, status=400)

    texto = (
        "🐾 Nueva cita\n\n"
        f"Dueño: {datos['dueno']}\n"
        f"Mascota: {datos['mascota']} ({datos['especie']})\n"
        f"Servicio: {datos['servicio']}\n"
        f"Fecha: {datos['fecha']}\n"
        f"Hora: {datos['hora']}\n"
        f"Teléfono: {datos['telefono']}"
    )

    try:
        r = requests.post(
            f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": settings.TELEGRAM_CHAT_ID, "text": texto},
            timeout=10,
        )
        r.raise_for_status()
    except requests.RequestException:
        return JsonResponse({"ok": False, "error": "No se pudo enviar"}, status=502)

    return JsonResponse({"ok": True})

