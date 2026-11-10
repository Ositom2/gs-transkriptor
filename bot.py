import os
import threading
from flask import Flask
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

# 1. Configurar Flask para mantener el servicio activo en Render
app = Flask(__name__)

@app.route('/')
def home():
    return "¡Bot en línea y funcionando!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# 2. Configurar el Bot de Telegram y los manejadores
async def start(update, context):
    await update.message.reply_text("¡Hola! Envíame un archivo de audio y te generaré su transcripción en PDF.")

def main():
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        print("Error: TELEGRAM_TOKEN no está configurado.")
        return

    # Iniciar Flask en un hilo separado (para que no bloquee el bot)
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Iniciar el bot de Telegram con polling
    application = ApplicationBuilder().token(token).build()
    
    application.add_handler(CommandHandler("start", start))
    
    print("Bot iniciado y escuchando...")
    application.run_polling()

if __name__ == '__main__':
    main()
