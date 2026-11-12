import os
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters
import google.generativeai as genai

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configurar Gemini
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# Leer el token y verificar que exista
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("BOT_TOKEN")

if not TOKEN:
    logger.error("¡ERROR CRÍTICO! No se encontró ningún token de Telegram en las variables de entorno.")
    exit(1)

application = Application.builder().token(TOKEN).updater(None).build()

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Procesando tu audio...")

application.add_handler(MessageHandler(filters.AUDIO | filters.VOICE | filters.Document.ALL, handle_audio))

@app.route('/')
def home():
    return "Bot activo y funcionando"

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    import asyncio
    update = Update.de_json(request.get_json(force=True), application.bot)
    async def process():
        await application.initialize()
        await application.process_update(update)
    asyncio.run(process())
    return "ok"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
