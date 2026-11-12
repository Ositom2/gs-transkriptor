import os
import logging
import tempfile
import asyncio
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters
from google import genai

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else genai.Client()

TOKEN = os.environ.get("TELEGRAM_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("BOT_TOKEN")

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    audio_file = message.audio or message.voice or message.document
    
    if not audio_file:
        await message.reply_text("Por favor, envía un archivo de audio o nota de voz.")
        return

    sent_msg = await message.reply_text("📥 [1/3] Descargando audio desde Telegram...")

    temp_audio_path = None
    try:
        file_obj = await context.bot.get_file(audio_file.file_id)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
            await file_obj.download_to_drive(temp_audio.name)
            temp_audio_path = temp_audio.name

        await sent_msg.edit_text("⬆️ [2/3] Subiendo y procesando con Gemini...")

        def process_audio():
            # Subir archivo usando el cliente oficial
            uploaded_file = client.files.upload(file=temp_audio_path)
            # Generar transcripción
            return client.models.generate_content(
                model="gemini-3.8-flash",
                contents=[
                    uploaded_file, 
                    "Genera una transcripción detallada, limpia y fiel de este audio en formato de texto."
                ]
            )

        # Ejecutar en hilo separado con asyncio para no congelar el bot
        response = await asyncio.to_thread(process_audio)
        
        if temp_audio_path and os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
        
        transcript_text = response.text
        if len(transcript_text) > 4000:
            transcript_text = transcript_text[:4000] + "\n...(cortado por longitud)"
            
        await sent_msg.edit_text(f"📝 [3/3] **Transcripción exitosa:**\n\n{transcript_text}")

    except Exception as e:
        if temp_audio_path and os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
        logger.error(f"Error procesando audio: {e}")
        await sent_msg.edit_text(f"❌ Ocurrió un error: {str(e)}")

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.AUDIO | filters.VOICE | filters.Document.ALL, handle_audio))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: u.message.reply_text("Envíame un audio para transcribirlo.")))
    
    logger.info("Iniciando bot con indicadores de progreso...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
