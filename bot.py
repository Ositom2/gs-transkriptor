import os
import logging
import tempfile
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters
import google.generativeai as genai

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

TOKEN = os.environ.get("TELEGRAM_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("BOT_TOKEN")

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    audio_file = message.audio or message.voice or message.document
    
    if not audio_file:
        await message.reply_text("Por favor, envía un archivo de audio o nota de voz.")
        return

    await message.reply_text("📥 Audio recibido. Descargando y procesando con Gemini...")

    try:
        # Descargar archivo de Telegram
        file_obj = await context.bot.get_file(audio_file.file_id)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
            await file_obj.download_to_drive(temp_audio.name)
            temp_audio_path = temp_audio.name

        # Subir y procesar con Gemini
        await message.reply_text("🤖 Transcribiendo audio con Inteligencia Artificial...")
        
        gemini_file = genai.upload_file(temp_audio_path)
        
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content([
            gemini_file, 
            "Genera una transcripción detallada y limpia de este audio en formato de texto."
        ])
        
        # Limpiar archivo temporal local
        os.remove(temp_audio_path)
        
        # Enviar el resultado al usuario
        transcript_text = response.text
        if len(transcript_text) > 4000:
            transcript_text = transcript_text[:4000] + "\n...(cortado por longitud)"
            
        await message.reply_text(f"📝 **Transcripción:**\n\n{transcript_text}")

    except Exception as e:
        logger.error(f"Error procesando audio: {e}")
        await message.reply_text(f"❌ Ocurrió un error al procesar el audio: {str(e)}")

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.AUDIO | filters.VOICE | filters.DOCUMENT, handle_audio))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: u.message.reply_text("Envíame un audio o nota de voz para transcribirlo.")))
    
    logger.info("Iniciando bot en modo Polling con soporte de audio...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
