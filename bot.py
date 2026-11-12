import os
import logging
import tempfile
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters
from google import genai

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar el cliente moderno de Google GenAI
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else genai.Client()

TOKEN = os.environ.get("TELEGRAM_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("BOT_TOKEN")

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    audio_file = message.audio or message.voice or message.document
    
    if not audio_file:
        await message.reply_text("Por favor, envía un archivo de audio o nota de voz.")
        return

    await message.reply_text("📥 Audio recibido. Descargando y procesando...")

    try:
        file_obj = await context.bot.get_file(audio_file.file_id)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
            await file_obj.download_to_drive(temp_audio.name)
            temp_audio_path = temp_audio.name

        await message.reply_text("🤖 Transcribiendo audio con Gemini...")
        
        # Subir archivo usando el cliente moderno
        uploaded_file = client.files.upload(file=temp_audio_path)
        
        # Generar transcripción con gemini-2.5-flash
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                uploaded_file, 
                "Genera una transcripción detallada y limpia de este audio en formato de texto."
            ]
        )
        
        os.remove(temp_audio_path)
        
        transcript_text = response.text
        if len(transcript_text) > 4000:
            transcript_text = transcript_text[:4000] + "\n...(cortado por longitud)"
            
        await message.reply_text(f"📝 **Transcripción:**\n\n{transcript_text}")

    except Exception as e:
        logger.error(f"Error procesando audio: {e}")
        await message.reply_text(f"❌ Ocurrió un error al procesar el audio: {str(e)}")

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.AUDIO | filters.VOICE | filters.Document.ALL, handle_audio))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: u.message.reply_text("Envíame un audio o nota de voz para transcribirlo.")))
    
    logger.info("Iniciando bot con cliente moderno de Google GenAI...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
