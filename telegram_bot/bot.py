import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
from config import Config
from .handlers import start, reservar, mis_reservas, cancelar, menu, handle_message, handle_callback

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def post_init(application):
    """Post-initialization hook."""
    await application.bot.set_my_commands([
        ('start', 'Iniciar el bot'),
        ('reservar', 'Hacer una reserva'),
        ('mis_reservas', 'Ver mis reservas'),
        ('cancelar', 'Cancelar reserva'),
        ('menu', 'Ver el menú')
    ])

def main():
    """Start the bot."""
    application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).post_init(post_init).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("reservar", reservar))
    application.add_handler(CommandHandler("mis_reservas", mis_reservas))
    application.add_handler(CommandHandler("cancelar", cancelar))
    application.add_handler(CommandHandler("menu", menu))
    
    # Conversation handler for natural language
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)],
        states={},
        fallbacks=[],
    )
    application.add_handler(conv_handler)
    
    # Callback query handler for inline buttons
    application.add_handler(CallbackQueryHandler(handle_callback))

    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()