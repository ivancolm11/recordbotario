from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from models import session, RegistroAgua, RegistroComida
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, date
from twilio.rest import Client
import os 


app = Flask(__name__)
    

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "US1b134915fea6719939fc5177aae14b7c")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "b81db3991b21a02814cc6c7b6b8a9fca")
FROM_WHATSAPP = os.getenv("TWILIO_FROM_WHATSAPP", "whatsapp:+14155238886")  # Número Sandbox de Twilio
TO_WHATSAPP = os.getenv("TWILIO_TO_WHATSAPP", "whatsapp:+5491127170193")  # tu número con prefijo país

twilio_client = Client(ACCOUNT_SID, AUTH_TOKEN)


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
        resumen += "\n🍽️ Detalle comidas:\n"
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
        # Intenta limpiar y convertir a float (maneja comas/puntos decimales)
        palabra_limpia = palabra.replace('.', '').replace(',', '')
        if palabra_limpia.isdigit():
            # Devuelve el float original, incluyendo cualquier punto decimal
            try:
                return float(palabra.replace(',', '.'))
            except ValueError:
                continue
        elif palabra.replace('.', '', 1).isdigit():
             return float(palabra)
    return None

def extraer_comida(texto):
    # Buscar el separador de descripción/calorías, generalmente una coma
    partes = texto.split(',')
    
    # Caso 1: Se usa el formato 'Comí [descripción], [cantidad] cal'
    if len(partes) >= 2:
        descripcion = partes[0].replace("comí", "").strip()
        calorias = extraer_numero(partes[1])
        return descripcion, calorias
    
    # Caso 2: Intenta extraer del texto completo (menos robusto)
    elif "cal" in texto or "kcal" in texto:
        calorias = extraer_numero(texto)
        if calorias:
            # Si se encuentra caloría, intenta extraer descripción (todo lo que no es número o unidad)
            descripcion = texto.replace("comí", "").replace(str(int(calorias)), "").replace("cal", "").replace("kcal", "").strip()
            return descripcion, calorias
    
    return None, None

def generar_resumen():
    # El resumen general consulta todos los datos, no solo los de hoy.
    agua_total = sum(a.cantidad_ml for a in session.query(RegistroAgua).all())
    comidas = session.query(RegistroComida).all()
    total_cal = sum(c.calorias for c in comidas)
    resumen = (
        f"📊 Resumen general:\n"
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
    if "agua" in incoming_msg or "tomé" in incoming_msg and ("ml" in incoming_msg or "litros" in incoming_msg):
        cantidad = extraer_numero(incoming_msg)
        
        # Si la cantidad está en litros, la convierte a ml
        if "litros" in incoming_msg and cantidad is not None:
             cantidad *= 1000

        if cantidad:
            registro = RegistroAgua(cantidad_ml=cantidad)
            session.add(registro)
            session.commit()
            msg.body(f" Registré {cantidad:.0f} ml de agua. ¡Bien hecho!")
        else:
            msg.body(" Decime cuánta agua tomaste (ejemplo: 'Tomé 500 ml de agua').")

    # Registrar comida
    elif "comí" in incoming_msg or "comida" in incoming_msg:
        descripcion, calorias = extraer_comida(incoming_msg)
        if descripcion and calorias:
            registro = RegistroComida(descripcion=descripcion, calorias=calorias)
            session.add(registro)
            session.commit()
            msg.body(f" Registré '{descripcion}' con {calorias:.0f} calorías.")
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
                texto += f"- {hora_comida}: {c.descripcion} ({c.calorias:.0f} kcal)\n"
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
        msg.body(" Hola! Puedo registrar agua o comidas.\n"
                 "- 'Tomé 500 ml de agua' o 'Tomé 1.5 litros de agua'\n"
                 "- 'Comí pasta, 650 cal'\n"
                 "- 'Agua hoy' para ver lo que tomaste hoy\n"
                 "- 'Comidas hoy' para ver comidas y calorías de hoy\n"
                 "- 'Resumen' para ver tu progreso total")

    return str(resp)

# --- Ejecutar Flask ---
if __name__ == "__main__":
    # En Azure, Gunicorn se encarga de ejecutar la aplicación, 
    # pero este bloque es útil para pruebas locales.
    app.run(host="0.0.0.0", port=5000)