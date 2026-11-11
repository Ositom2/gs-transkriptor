import os
import threading
import tempfile
from flask import Flask
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
import google.generativeai as genai
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# 1. Configurar Flask para mantener el servicio activo en Render
app = Flask(__name__)

@app.route('/')
def home():
    return "¡Bot en línea y funcionando!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# 2. Configurar la API de Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

async def start(update, context):
    await update.message.reply_text("¡Hola! Envíame un archivo de audio y te generaré su transcripción en PDF.")

def generar_pdf(texto, ruta_pdf):
    doc = SimpleDocTemplate(ruta_pdf, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    
    estilo_texto = ParagraphStyle(
        'EstiloTranscripcion',
        parent=styles['Normal'],
        fontSize=11,
        leading=16,
        textColor=colors.HexColor('#222222')
    )
    
    story = [Paragraph("<b>Transcripción de Audio</b>", styles['Title']), Spacer(1, 15)]
    
    for parrafo in texto.split('\n'):
        if parrafo.strip():
            story.append(Paragraph(parrafo.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'), estilo_texto))
            story.append(Spacer(1, 8))
            
    doc.build(story)

async def manejar_audio(update, context):
    mensaje = await update.message.reply_text("📥 Descargando y procesando el audio con Gemini...")
    
    try:
        archivo_telegram = await update.message.audio.get_file()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            ruta_audio = os.path.join(temp_dir, "audio_temp.mp3")
            await archivo_telegram.download_to_drive(ruta_audio)
            
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=mensaje.message_id,
                text="🎙️ Transcribiendo audio con IA (esto puede tomar un momento)..."
            )
            
            audio_ref = genai.upload_file(ruta_audio)
            modelo = genai.GenerativeModel('gemini-1.5-flash')
            respuesta = modelo.generate_content([
                audio_ref, 
                "Por favor, transcribe este audio de manera detallada y clara."
            ])
            
            texto_transcrito = respuesta.text
            
            ruta_pdf = os.path.join(temp_dir, "transcripcion.pdf")
            generar_pdf(texto_transcrito, ruta_pdf)
            
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=mensaje.message_id,
                text="📄 ¡Transcripción lista! Enviando documento..."
            )
            
            with open(ruta_pdf, 'rb') as pdf_file:
                await update.message.reply_document(
                    document=pdf_file,
                    filename="transcripcion.pdf",
                    caption="Aquí tienes la transcripción completa en PDF."
                )
                
    except Exception as e:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=mensaje.message_id,
            text=f"❌ Ocurrió un error al procesar el audio: {str(e)}"
        )

def main():
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        print("Error: TELEGRAM_TOKEN no está configurado.")
        return

    # Iniciar Flask en un hilo separado
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Iniciar el bot de Telegram
    application = ApplicationBuilder().token(token).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.AUDIO | filters.VOICE | filters.Document.AUDIO, manejar_audio))
    
    print("Bot iniciado y escuchando...")
    application.run_polling()

if __name__ == '__main__':
    main()
