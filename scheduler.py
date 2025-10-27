from apscheduler.schedulers.background import BackgroundScheduler
from twilio.rest import Client
from datetime import datetime
import time

# Configura tus credenciales de Twilio (desde tu cuenta)
ACCOUNT_SID = "US1b134915fea6719939fc5177aae14b7c"
AUTH_TOKEN = "b81db3991b21a02814cc6c7b6b8a9fca"
FROM_WHATSAPP = "whatsapp:+14155238886"  # número de Twilio Sandbox
TO_WHATSAPP = "whatsapp:+5491127170193"  # tu número con prefijo país

client = Client(ACCOUNT_SID, AUTH_TOKEN)

def enviar_mensaje(texto):
    client.messages.create(
        from_=FROM_WHATSAPP,
        body=texto,
        to=TO_WHATSAPP
    )

def recordar_agua():
    enviar_mensaje(" ¿Tomaste agua en esta última hora? Decime cuántos ml si ya lo hiciste.")

def preguntar_comida():
    hora = datetime.now().strftime("%H:%M")
    enviar_mensaje(f" Son las {hora}. ¿Qué comiste y cuántas calorías aprox?")

def iniciar_scheduler():
    scheduler = BackgroundScheduler()
    # Cada hora recordatorio de agua
    scheduler.add_job(recordar_agua, 'interval', hours=1)
    # Recordatorios de comida
    scheduler.add_job(preguntar_comida, 'cron', hour=8)
    scheduler.add_job(preguntar_comida, 'cron', hour=13)
    scheduler.add_job(preguntar_comida, 'cron', hour=20)
    scheduler.start()
    print(" Scheduler iniciado...")

if __name__ == "__main__":
    iniciar_scheduler()
    while True:
        time.sleep(60)
