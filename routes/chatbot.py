from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from chatbot.conversation import ConversationManager

chatbot_bp = Blueprint('chatbot', __name__, template_folder='templates')

@chatbot_bp.route('/chatbot')
@login_required
def chatbot_interface():
    """Interfaz web para el chatbot."""
    return render_template('chatbot.html')

@chatbot_bp.route('/chatbot/converse', methods=['POST'])
@login_required
def converse():
    """Endpoint para conversación con el chatbot."""
    try:
        user_message = request.json.get('message')
        if not user_message:
            return jsonify({'response': 'Mensaje requerido. Por favor, envía un mensaje válido.'}), 400

        # Sanitización básica de input
        import re
        user_message = re.sub(r'<script.*?</script>', '', user_message, flags=re.DOTALL)
        user_message = re.sub(r'on\w+[\s]*=', '', user_message)  # Remove event handlers

        # Crear manager con user_id
        manager = ConversationManager(current_user.id)

        response = manager.process_message(user_message)
        action_data = None  # No actions implemented yet

        return jsonify({
            'response': response if response else 'No pude generar una respuesta. Intenta de nuevo.',
            'conversation_id': str(current_user.id),
            'action': action_data
        })
    except Exception as e:
        import traceback
        error_msg = f"Error interno: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)  # Log para depuración
        return jsonify({'response': 'Error al procesar el mensaje. Verifica que Ollama esté ejecutándose y prueba de nuevo.'}), 500