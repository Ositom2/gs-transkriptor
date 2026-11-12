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
# Inicializar el cliente asegurando que tome la API Key correcta
client = genai.Client(api_key=api_key) if api_key else genai.Client()

TOKEN = os.environ.get("TELEGRAM_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("BOT_TOKEN")

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    audio_file = message.audio or message.voice or message.document
    
    if not audio_file:
        await message.reply_text("Por favor, envía un archivo de audio o nota de voz.")
        return

    sent_msg = await message.reply_text("📥 Audio recibido. Descargando...")

    temp_audio_path = None
    try:
        file_obj = await context.bot.get_file(audio_file.file_id)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
            await file_obj.download_to_drive(temp_audio.name)
            temp_audio_path = temp_audio.name

        await sent_msg.edit_text("🤖 Procesando con tu cuenta Pro/Pagada...")

        def process_with_gemini():
            uploaded_file = client.files.upload(file=temp_audio_path)
            # Usar el modelo Pro o Flash configurado con tu cuota de pago
            return client.models.generate_content(
                model="gemini-3.8-flash",
                contents=[
                    uploaded_file, 
                    "Genera una transcripción detallada, limpia y fiel de este audio en formato de texto."
                ]
            )

        response = await asyncio.wait_for(asyncio.to_thread(process_with_gemini), timeout=90.0)
        
        if temp_audio_path and os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
        
        transcript_text = response.text
        if len(transcript_text) > 4000:
            transcript_text = transcript_text[:4000] + "\n...(cortado por longitud)"
            
        await sent_msg.edit_text(f"📝 **Transcripción (Plan Pagado):**\n\n{transcript_text}")

    except asyncio.TimeoutError:
        if temp_audio_path and os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
        logger.error("Timeout procesando audio con Gemini")
        await sent_msg.edit_text("❌ El servidor tardó demasiado. Intenta de nuevo.")
    except Exception as e:
        if temp_audio_path and os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
        logger.error(f"Error procesando audio: {e}")
        await sent_msg.edit_text(f"❌ Ocurrió un error: {str(e)}")

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.AUDIO | filters.VOICE | filters.Document.ALL, handle_audio))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: u.message.reply_text("Envíame un audio o nota de voz para transcribirlo.")))
    
    logger.info("Iniciando bot con plan pagado...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
