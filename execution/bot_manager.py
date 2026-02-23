import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from directives.messages import START_MESSAGE, CNC_STATUS_IDLE

# Configurar logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Responde al comando /start."""
    user = update.effective_user
    await update.message.reply_html(
        START_MESSAGE.format(mention=user.mention_html()),
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Responde al comando /status con el estado de la CNC."""
    # En el futuro, aquí conectaremos con la clase que controla la CNC real
    await update.message.reply_text(f"Estado de la CNC: {CNC_STATUS_IDLE}")

def run_bot(token: str) -> None:
    """Inicia el bot y espera por comandos."""
    application = Application.builder().token(token).build()

    # Registrar los manejadores de comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))

    print("🚀 Bot iniciado desde execution/bot_manager. Presiona Ctrl+C para detenerlo.")
    application.run_polling()