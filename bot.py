import os
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters
import google.generativeai as genai

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

TOKEN = os.environ.get("TELEGRAM_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("BOT_TOKEN")

application = Application.builder().token(TOKEN).updater(None).build()

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Audio recibido. Procesando...")

application.add_handler(MessageHandler(filters.ALL, handle_audio))

@app.route('/')
def home():
    return "Bot activo"

@app.route('/webhook', methods=["POST"])
def webhook():
    import asyncio
    json_data = request.get_json(force=True)
    logger.info(f"Mensaje recibido de Telegram: {json_data}")
    update = Update.de_json(json_data, application.bot)
    async def process():
        await application.initialize()
        await application.process_update(update)
    asyncio.run(process())
    return "ok"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
