import os
import logging
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import google.generativeai as genai

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuración de Flask para mantener el servicio activo en Render
app = Flask(__name__)

@app.route('/')
def home():
    return "¡Bot Transcriptor de Audio a PDF activo y funcionando!"

# Configuración de la API de Gemini
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    logger.error("No se encontró la variable de entorno GEMINI_API_KEY.")
else:
    genai.configure(api_key=api_key)

# Inicializar el modelo optimizado
model = genai.GenerativeModel("gemini-1.5-flash")

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Aquí va tu lógica para descargar el audio, procesarlo con el modelo y generar el PDF
    await update.message.reply_text("Procesando tu audio...")

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

def main():
    # Obtener el token del bot de Telegram desde las variables de entorno
    telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not telegram_token:
        logger.error("No se encontró el TELEGRAM_BOT_TOKEN.")
        return

    application = ApplicationBuilder().token(telegram_token).build()

    # Manejador para audios, notas de voz y documentos
    application.add_handler(MessageHandler(filters.AUDIO | filters.VOICE | filters.Document.ALL, handle_audio))

    # Iniciar el bot en modo polling
    application.run_polling()

if __name__ == '__main__':
    import threading
    # Ejecutar Flask en un hilo separado para cumplir con el requisito de puertos de Render
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    
    # Iniciar Telegram Bot
    main()
