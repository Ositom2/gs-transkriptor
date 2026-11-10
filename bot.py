import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
import google.generativeai as genai
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from flask import Flask
from threading import Thread

# Configuración de las APIs
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

# Servidor Flask para mantener el bot despierto en Render
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "¡Bot en línea y funcionando!"

def run_flask():
    app_flask.run(host="0.0.0.0", port=10000)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

def crear_pdf_predica(texto, nombre_archivo="Predica.pdf"):
    c = canvas.Canvas(nombre_archivo, pagesize=letter)
    ancho, alto = letter
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(ancho / 2, alto - 40, "Transcripción de Predica")
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Hola! Envíame un audio o nota de voz y te lo transcribiré a PDF.")

async def manejar_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = update.message
    audio = mensaje.audio or mensaje.voice
    if not audio:
        await mensaje.reply_text("Envíame un audio válido.")
        return

    status = await mensaje.reply_text("🎧 Procesando...")
    try:
        f = await context.bot.get_file(audio.file_id)
        await f.download_to_drive("temp_audio.mp3")

        audio_ref = genai.upload_file("temp_audio.mp3")
        modelo = genai.GenerativeModel("gemini-1.5-flash")
        resp = modelo.generate_content(["Transcribe este audio exactamente en texto:", audio_ref])

        pdf = crear_pdf_predica(resp.text)
        await mensaje.reply_document(document=open(pdf, "rb"))
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
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.AUDIO | filters.VOICE | filters.Document.AUDIO, manejar_audio))
    print("🚀 ¡BOT EN LÍNEA EN RENDER!")

    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
