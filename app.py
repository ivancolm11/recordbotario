from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from models import session, RegistroAgua, RegistroComida
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, date
from twilio.rest import Client
import os # <-- AÑADIDO PARA LEER VARIABLES DE ENTORNO

# --- Configuración Flask ---
app = Flask(__name__)
    
# --- Configuración Twilio (AHORA USANDO os.getenv) ---
# Si no encuentra la variable de entorno, usa el valor por defecto (hardcodeado)
ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "US1b134915fea6719939fc5177aae14b7c") 
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "b81db3991b21a02814cc6c7b6b8a9fca") 
FROM_WHATSAPP = os.getenv("TWILIO_FROM_WHATSAPP", "whatsapp:+14155238886") 
TO_WHATSAPP = os.getenv("TWILIO_TO_WHATSAPP", "whatsapp:+5491127170193") 

twilio_client = Client(ACCOUNT_SID, AUTH_TOKEN)

# --- Funciones de recordatorio y envío ---
def enviar_mensaje(texto):
    twilio_client.messages.create(
        from_=FROM_WHATSAPP,
        body=texto,
        to=TO_WHATSAPP
    )

def recordar_agua():
    enviar_mensaje(" ¿Tomaste agua en esta última hora? Decime cuántos ml si ya lo hiciste.")

def preguntar_comida():
    hora = datetime.now().strftime("%H:%M")
    enviar_mensaje(f" Son las {hora}. ¿Qué comiste y cuántas calorías aprox? (ej: 'Comí pasta, 650 cal')")

def resumen_diario():
    hoy = date.today()
    # Aseguramos que la sesión está disponible para consulta
    from models import session # Reimportamos para asegurar que la sesión es la correcta después del inicio
    agua_total = sum(a.cantidad_ml for a in session.query(RegistroAgua)
                     .filter(RegistroAgua.fecha >= datetime.combine(hoy, datetime.min.time())).all())
    comidas = session.query(RegistroComida)\
                     .filter(RegistroComida.fecha >= datetime.combine(hoy, datetime.min.time())).all()
    total_cal = sum(c.calorias for c in comidas)

    resumen = (
        f" Resumen diario ({hoy.strftime('%d/%m/%Y')}):\n"
        f"- Agua total: {agua_total:.0f} ml\n"
        f"- Comidas registradas: {len(comidas)}\n"
        f"- Calorías totales: {total_cal:.0f} kcal\n"
    )

    if comidas:
        resumen += "\n Detalle comidas:\n"
        for c in comidas:
            hora_comida = c.fecha.strftime("%H:%M")
            resumen += f"- {hora_comida}: {c.descripcion} ({c.calorias} kcal)\n"

    enviar_mensaje(resumen)

# --- Configuración APScheduler ---
scheduler = BackgroundScheduler()

# Recordatorio de agua cada hora
scheduler.add_job(recordar_agua, 'interval', hours=1)

# Recordatorios de comida (modifica los horarios según prefieras)
scheduler.add_job(preguntar_comida, 'cron', hour=8)
scheduler.add_job(preguntar_comida, 'cron', hour=13)
scheduler.add_job(preguntar_comida, 'cron', hour=20)

# Resumen diario automático a las 22:00 (modifica si querés otra hora)
scheduler.add_job(resumen_diario, 'cron', hour=22, minute=0)

scheduler.start()

# --- Funciones auxiliares ---
def extraer_numero(texto):
    for palabra in texto.split():
        if palabra.isdigit():
            return float(palabra)
        elif palabra.replace('.', '', 1).isdigit():
            return float(palabra)
    return None

def extraer_comida(texto):
    partes = texto.split(',')
    if len(partes) >= 2:
        descripcion = partes[0].replace("comí", "").strip()
        calorias = extraer_numero(partes[1])
        return descripcion, calorias
    return None, None

def generar_resumen():
    agua_total = sum(a.cantidad_ml for a in session.query(RegistroAgua).all())
    comidas = session.query(RegistroComida).all()
    total_cal = sum(c.calorias for c in comidas)
    resumen = (
        f" Resumen general:\n"
        f"- Agua total: {agua_total:.0f} ml\n"
        f"- Comidas registradas: {len(comidas)}\n"
        f"- Calorías totales: {total_cal:.0f} kcal"
    )
    return resumen

# --- Webhook de WhatsApp ---
@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    incoming_msg = request.values.get('Body', '').strip().lower()
    resp = MessagingResponse()
    msg = resp.message()

    # Registrar agua
    if "agua" in incoming_msg:
        cantidad = extraer_numero(incoming_msg)
        if cantidad:
            registro = RegistroAgua(cantidad_ml=cantidad)
            session.add(registro)
            session.commit()
            msg.body(f" Registré {cantidad} ml de agua. ¡Bien hecho!")
        else:
            msg.body(" Decime cuánta agua tomaste (ejemplo: 'Tomé 500 ml de agua').")

    # Registrar comida
    elif "comí" in incoming_msg or "comida" in incoming_msg:
        descripcion, calorias = extraer_comida(incoming_msg)
        if descripcion and calorias:
            registro = RegistroComida(descripcion=descripcion, calorias=calorias)
            session.add(registro)
            session.commit()
            msg.body(f" Registré '{descripcion}' con {calorias} calorías.")
        else:
            msg.body(" Decime qué comiste y cuántas calorías aprox. (ej: 'Comí pasta, 650 cal').")

    # Consultar agua del día
    elif "agua hoy" in incoming_msg:
        hoy = datetime.now().date()
        agua_total = sum(a.cantidad_ml for a in session.query(RegistroAgua)
                         .filter(RegistroAgua.fecha >= datetime.combine(hoy, datetime.min.time()))
                         .all())
        msg.body(f" Agua consumida hoy: {agua_total:.0f} ml")

    # Consultar comidas del día
    elif "comidas hoy" in incoming_msg:
        hoy = datetime.now().date()
        comidas = session.query(RegistroComida)\
                         .filter(RegistroComida.fecha >= datetime.combine(hoy, datetime.min.time()))\
                         .all()
        if comidas:
            texto = f" Comidas de hoy ({hoy.strftime('%d/%m/%Y')}):\n"
            total_cal = 0
            for c in comidas:
                hora_comida = c.fecha.strftime("%H:%M")
                texto += f"- {hora_comida}: {c.descripcion} ({c.calorias} kcal)\n"
                total_cal += c.calorias
            texto += f" Calorías totales hoy: {total_cal:.0f} kcal"
        else:
            texto = " No registraste comidas hoy."
        msg.body(texto)

    # Resumen general
    elif "resumen" in incoming_msg:
        resumen = generar_resumen()
        msg.body(resumen)

    # Mensaje por defecto
    else:
        msg.body("👋 Hola! Puedo registrar agua o comidas.\n"
                 "- 'Tomé 500 ml de agua'\n"
                 "- 'Comí pasta, 650 cal'\n"
                 "- 'Agua hoy' para ver lo que tomaste hoy\n"
                 "- 'Comidas hoy' para ver comidas y calorías de hoy\n"
                 "- 'Resumen' para ver tu progreso total")

    return str(resp)

# --- Ejecutar Flask ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)