import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config import Config
from chatbot.conversation import ConversationManager
from chatbot.ollama_client import OllamaClient
from models.database import db
from models.user import User
from models.reservation import Reserva, Mesa
from models.menu import Plato, Bebida
from utils.calendar_helper import get_horarios_disponibles, get_mesas_disponibles, validar_reserva
from utils.email_sender import enviar_confirmacion_reserva
from datetime import datetime

logger = logging.getLogger(__name__)

# Estados para ConversationHandler
WAITING_EMAIL, WAITING_DATE, WAITING_TIME, WAITING_PEOPLE, WAITING_CONFIRM = range(5)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start."""
    keyboard = [
        [InlineKeyboardButton("Reservar Mesa", callback_data='reservar')],
        [InlineKeyboardButton("Ver Menú", callback_data='menu')],
        [InlineKeyboardButton("Mis Reservas", callback_data='mis_reservas')],
        [InlineKeyboardButton("Cancelar Reserva", callback_data='cancelar')],
        [InlineKeyboardButton("Chatbot IA", callback_data='chatbot')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        '¡Bienvenido a Sabores y Raíces! Soy tu asistente para reservas y más.\n'
        'Elige una opción:',
        reply_markup=reply_markup
    )
    return ConversationHandler.END

async def reservar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /reservar - inicia flujo de reserva."""
    await update.message.reply_text(
        'Para hacer una reserva, necesito tu email (para asociar con tu cuenta). '
        'Si no tienes cuenta, proporciona uno para crear.',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancelar", callback_data='cancel')]])
    )
    return WAITING_EMAIL

async def mis_reservas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /mis_reservas - muestra reservas del usuario."""
    telegram_id = update.effective_user.id
    # Buscar usuario por telegram_id o pedir email
    user = User.query.filter_by(telegram_id=telegram_id).first()
    if not user:
        await update.message.reply_text('Por favor, proporciona tu email para ver reservas.')
        return WAITING_EMAIL  # Reutilizar estado

    reservas = Reserva.query.filter_by(usuario_id=user.id, estado='confirmada').all()
    if not reservas:
        await update.message.reply_text('No tienes reservas activas.')
        return ConversationHandler.END

    text = 'Tus reservas:\n'
    for r in reservas:
        text += f"#{r.id}: {r.fecha_reserva} a las {r.hora_reserva} - Mesa {r.mesa.numero_mesa} para {r.num_comensales} personas\n"
    await update.message.reply_text(text)
    return ConversationHandler.END

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /cancelar - cancela reserva."""
    telegram_id = update.effective_user.id
    user = User.query.filter_by(telegram_id=telegram_id).first()
    if not user:
        await update.message.reply_text('Por favor, proporciona tu email para cancelar.')
        return WAITING_EMAIL

    reservas = Reserva.query.filter_by(usuario_id=user.id, estado='confirmada').all()
    if not reservas:
        await update.message.reply_text('No tienes reservas para cancelar.')
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton(f"#{r.id} - {r.fecha_reserva}", callback_data=f"cancel_{r.id}")] for r in reservas]
    keyboard.append([InlineKeyboardButton("Cancelar", callback_data='cancel')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Selecciona la reserva a cancelar:', reply_markup=reply_markup)
    return ConversationHandler.END

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /menu - muestra menú con botones."""
    platos = Plato.query.filter_by(disponible=True).all()
    bebidas = Bebida.query.filter_by(disponible=True).all()

    text = "🍽️ **Menú del Día**\n\n**Platos Principales:**\n"
    for p in platos[:5]:  # Limitar para no sobrecargar
        text += f"• {p.nombre} - ${p.precio}\n"

    text += "\n**Bebidas:**\n"
    for b in bebidas[:5]:
        text += f"• {b.nombre} - ${b.precio}\n"

    text += "\nUsa /chatbot para recomendaciones personalizadas."

    keyboard = [
        [InlineKeyboardButton("Ver Platos Completos", callback_data='menu_platos')],
        [InlineKeyboardButton("Ver Bebidas", callback_data='menu_bebidas')],
        [InlineKeyboardButton("Chatbot IA", callback_data='chatbot')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    return ConversationHandler.END

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja mensajes de texto para conversación natural."""
    message = update.message.text
    telegram_id = update.effective_user.id

    # Sanitización básica de input
    import re
    message = re.sub(r'<script.*?</script>', '', message, flags=re.DOTALL)
    message = re.sub(r'on\w+[\s]*=', '', message)  # Remove event handlers

    # Crear o recuperar manager
    manager = ConversationManager(telegram_id)  # Usar telegram_id como user_id temporal

    response, action_data = manager.process_message(message)

    await update.message.reply_text(response)

    # Si hay acción, manejar (ej. crear reserva)
    if action_data and action_data.get('intent') == 'reserva':
        # Lógica para confirmar y crear reserva via Telegram
        await update.message.reply_text('¡Reserva procesada! Confirma detalles en tu email.')

    return ConversationHandler.END

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja callbacks de botones inline."""
    query = update.callback_query
    await query.answer()

    data = query.data
    if data == 'reservar':
        await query.edit_message_text('Iniciando reserva...')
        await query.message.reply_text('Proporciona tu email:')
        return WAITING_EMAIL
    elif data == 'menu':
        await menu(update, context)
    elif data == 'mis_reservas':
        await mis_reservas(update, context)
    elif data == 'cancelar':
        await cancelar(update, context)
    elif data == 'chatbot':
        await query.edit_message_text('¡Hola! Soy el chatbot IA. ¿En qué puedo ayudarte?\n'
                                      'Pregúntame sobre reservas, menú o recomendaciones.')
        # Iniciar conversación natural
        return ConversationHandler.END
    elif data.startswith('cancel_'):
        reserva_id = int(data.split('_')[1])
        telegram_id = query.from_user.id
        user = User.query.filter_by(telegram_id=telegram_id).first()
        if user:
            reserva = Reserva.query.filter_by(id=reserva_id, usuario_id=user.id).first()
            if reserva:
                reserva.estado = 'cancelada'
                db.session.commit()
                await query.edit_message_text(f'Reserva #{reserva_id} cancelada.')
            else:
                await query.edit_message_text('Reserva no encontrada.')
        return ConversationHandler.END
    elif data == 'cancel':
        await query.edit_message_text('Operación cancelada.')
        return ConversationHandler.END

    # Para submenús del menú
    if data == 'menu_platos':
        platos = Plato.query.filter_by(disponible=True).all()
        text = '🍲 Platos disponibles:\n'
        for p in platos:
            text += f"• {p.nombre} - ${p.precio} ({p.categoria})\n"
        await query.edit_message_text(text)
    elif data == 'menu_bebidas':
        bebidas = Bebida.query.filter_by(disponible=True).all()
        text = '🥤 Bebidas disponibles:\n'
        for b in bebidas:
            text += f"• {b.nombre} - ${b.precio}\n"
        await query.edit_message_text(text)

async def handle_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja email proporcionado."""
    email = update.message.text.strip()
    telegram_id = update.effective_user.id

    # Buscar o crear usuario
    user = User.query.filter_by(email=email).first()
    if not user:
        # Crear usuario guest o pedir más info
        user = User(nombre=f"Usuario Telegram {telegram_id}", email=email, telefono=f"Telegram:{telegram_id}")
        user.set_password('default')  # Password dummy
        user.telegram_id = telegram_id
        db.session.add(user)
        db.session.commit()
        await update.message.reply_text('Cuenta creada. Ahora inicia reserva.')
    else:
        user.telegram_id = telegram_id
        db.session.commit()
        await update.message.reply_text('Cuenta asociada. ¿Qué deseas hacer?')

    # Continuar con reserva o mostrar menú
    keyboard = [
        [InlineKeyboardButton("Hacer Reserva", callback_data='reservar')],
        [InlineKeyboardButton("Ver Menú", callback_data='menu')],
        [InlineKeyboardButton("Mis Reservas", callback_data='mis_reservas')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Elige:', reply_markup=reply_markup)
    return ConversationHandler.END

# ConversationHandler para reserva
def get_reserva_conversation_handler():
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(reservar, pattern='^reservar$')],
        states={
            WAITING_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email)],
            WAITING_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_date)],
            # Añadir más estados para fecha, hora, etc.
        },
        fallbacks=[CommandHandler('cancelar', lambda u, c: ConversationHandler.END)],
    )

# Funciones adicionales para flujo de reserva (simplificadas)
async def handle_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Parse fecha, etc.
    await update.message.reply_text('Fecha recibida. Ahora proporciona hora (ej. 12:00 o 19:00).')
    return WAITING_TIME

# ... (implementar estados restantes similarmente)