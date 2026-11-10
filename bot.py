import os
import logging
import time
from flask import Flask
from threading import Thread
import nest_asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import google.generativeai as genai
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

nest_asyncio.apply()

#Configuración de tokens y credenciales
p1 = "9203844689:AAGsPlkc"
p2 = "zptgie_Z4AgoDipHc1nZ7e5B6p8"
TELEGRAM_TOKEN = p1 + p2
GEMINI_API_KEY = "AQ.Ab8RN6KXoD1gtnkEknlSVas68aeqpew5L-9Iw7WSpBdv0vKeWg"

genai.configure(api_key=GEMINI_API_KEY)
logging.basicConfig(level=logging.INFO)

#Servidor Flask mínimo para cumplir con Render y mantener el puerto abierto
app_flask = Flask('')

@app_flask.route('/')
def home():
    return "¡Bot de transcripción activo 24/7!"

def run_flask():
    app_flask.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

def crear_pdf_predica(texto, nombre_archivo="Predica_Transcripcion.pdf"):
    c = canvas.Canvas(nombre_archivo, pagesize=letter)
    ancho, alto = letter
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(ancho / 2, alto - 40, "Transcripción de Prédica GS")
    c.setFont("Helvetica", 11)

    y = alto - 85
    for parrafo in texto.split('\n'):
        c.drawString(54, y, parrafo[:90])
        y -= 20
        if y < 50:
            c.showPage()
            y = alto - 50
    c.save()
    return nombre_archivo

async def manejar_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = update.message
    audio = mensaje.audio or mensaje.voice
    if not audio:
    await mensaje.reply_text("Envíame un audio válido.")
    return
    
    status = await mensaje.reply_text("🎧 Procesando audio en la nube...")
    try:
    f = await context.bot.get_file(audio.file_id)
    await f.download_to_drive("temp_audio.mp3")
    
    audio_ref = genai.upload_file("temp_audio.mp3")
    modelo = genai.GenerativeModel("gemini-1.5-flash")
    resp = modelo.generate_content(["Transcribe esta prédica en español:", audio_ref])
    
    pdf = crear_pdf_predica(resp.text)
    await mensaje.reply_document(document=open(pdf, 'rb'), filename="Transcripcion.pdf")
    os.remove("temp_audio.mp3")
    os.remove(pdf)
    await status.delete()
    except Exception as e:
    await status.edit_text(f"❌ Error: {str(e)}")
    
def main():
# Levantar el servidor web para Render en segundo plano
keep_alive()

# Iniciar el bot de Telegram
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(MessageHandler(filters.AUDIO | filters.VOICE, manejar_audio))
print("🚀 ¡BOT EN LÍNEA EN RENDER!")

app.run_polling(drop_pending_updates=True)

if__name__=='__main__':
main()
