import os
import logging
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters
import google.generativeai as genai

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

TOKEN = os.environ.get("TELEGRAM_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("BOT_TOKEN")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Mensaje recibido en Telegram")
    await update.message.reply_text("¡Audio recibido y procesado correctamente!")

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.ALL, handle_message))
    
    logger.info("Iniciando bot en modo Polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
