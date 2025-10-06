from .ollama_client import OllamaClient
from models.database import db
from models.reservation import Reserva, Mesa
from models.menu import Plato, Bebida
from utils.calendar_helper import get_horarios_disponibles, get_mesas_disponibles, validar_reserva
from utils.email_sender import enviar_confirmacion_reserva
from datetime import datetime
import json
import re

class ConversationManager:
    def __init__(self, user_id):
        self.user_id = user_id
        self.ollama = OllamaClient()

    def process_message(self, message):
        # Prompt mejorado para siempre retornar JSON
        prompt = f"""
        Eres un asistente especializado en reservas de restaurante. Analiza el mensaje del usuario y responde SIEMPRE con JSON válido.

        REGLAS:
        1. Si el mensaje es sobre reserva (palabras: reservar, reserva, mesa, booking), usa intent: "reserva" y extrae datos.
        2. Para cualquier otro mensaje (preguntas generales, saludo, menú, etc.), usa intent: "general" y proporciona una respuesta útil en "response".
        3. SIEMPRE responde SOLO con JSON, sin texto adicional.

        FORMATO JSON OBLIGATORIO:
        {{
            "intent": "reserva" o "general",
            "response": "texto de respuesta natural" (siempre presente, incluso para reserva después de procesar),
            "fecha": "YYYY-MM-DD" (solo si intent=reserva),
            "hora": "HH:MM" (solo si intent=reserva),
            "num_comensales": número (solo si intent=reserva, default 2),
            "platos": [] (solo si intent=reserva),
            "bebidas": [] (solo si intent=reserva)
        }}

        INSTRUCCIONES PARA RESERVA (intent="reserva"):
        - Extrae fecha (YYYY-MM-DD, usa 2025 si no año, "mañana" = siguiente día).
        - Hora (HH:MM 24h, "8 PM" = "20:00").
        - Num comensales (default 2).
        - Platos y bebidas: listas de nombres mencionados.
        - Si falta fecha/hora, response = "Necesito fecha y hora para reservar."
        - Para reserva, response = mensaje de confirmación o error.

        PARA GENERAL (intent="general"):
        - response: Respuesta útil y amigable sobre el tema (menú, horarios, etc.).
        - Ej: Para "¿Qué platos hay?", response = "Tenemos paella, pizza, etc. ¿Quieres reservar?"

        EJEMPLOS:

        Usuario: "Hola"
        {{
            "intent": "general",
            "response": "¡Hola! Soy el asistente de Sabores y Raíces. ¿Quieres hacer una reserva o preguntar por el menú?"
        }}

        Usuario: "Reserva para 2 mañana a las 20:00"
        {{
            "intent": "reserva",
            "fecha": "2025-10-04",
            "hora": "20:00",
            "num_comensales": 2,
            "platos": [],
            "bebidas": [],
            "response": "Reserva confirmada para mañana a las 20:00 para 2 personas."
        }}

        Usuario: "¿Qué horarios?"
        {{
            "intent": "general",
            "response": "Estamos abiertos de 12:00-16:00 y 19:00-23:00. ¿Para reservar?"
        }}

        MENSAJE A ANALIZAR: {message}

        Responde SOLO con el JSON exacto.
        """

        ollama_response = self.ollama.generate_response(prompt)

        # Siempre parsear JSON
        try:
            data = json.loads(ollama_response)
            if data.get('intent') == 'reserva':
                # Procesar reserva como antes
                fecha_str = data.get('fecha')
                if not fecha_str or not data.get('hora'):
                    return data.get('response', 'Información incompleta para reserva.')
                
                hora_str = data.get('hora')
                num_comensales = data.get('num_comensales', 2)
                platos = data.get('platos', [])
                bebidas = data.get('bebidas', [])

                # Manejo de fecha
                if 'de ' in fecha_str:
                    meses_es = {
                        'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04', 'mayo': '05', 'junio': '06',
                        'julio': '07', 'agosto': '08', 'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
                    }
                    for mes, num in meses_es.items():
                        fecha_str = fecha_str.replace(mes, num)
                    if len(fecha_str.split('-')) < 3:
                        fecha_str = '2025-' + fecha_str
                    fecha_str = re.sub(r'(\d+)\s+de\s+(\d+)', r'\1-\2', fecha_str)
                
                try:
                    fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
                except ValueError:
                    return data.get('response', 'Fecha inválida.')

                # Limpieza y parseo robusto de hora con regex para extraer patrón HH:MM
                hora_str = re.sub(r'\s+', ' ', hora_str.strip()) if hora_str else ''  # Normalizar espacios
                print(f"Debug: Hora original de Ollama: '{hora_str}'")  # Log para depuración
                
                # Usar regex flexible para extraer HH:MM ignorando extras (espacios alrededor :)
                import re
                hora_match = re.search(r'(\d{1,2})\s*:\s*(\d{2})', hora_str)
                if hora_match:
                    hh = hora_match.group(1).zfill(2)
                    mm = hora_match.group(2)
                    hora_str = f"{hh}:{mm}"
                    print(f"Debug: Hora parseada: '{hora_str}'")  # Log
                else:
                    # Fallback: buscar dígitos y asumir formato
                    digits = re.findall(r'\d{1,2}', hora_str)
                    if len(digits) >= 2:
                        hh = digits[0].zfill(2)
                        mm = digits[1].zfill(2)
                        hora_str = f"{hh}:{mm}"
                        print(f"Debug: Hora fallback: '{hora_str}'")  # Log
                    else:
                        return data.get('response', f'No pude extraer la hora de "{hora_str}". Usa formato HH:MM como "12:00".')
                
                try:
                    hora = datetime.strptime(hora_str, '%H:%M').time()
                except ValueError as ve:
                    print(f"Debug: Error en strptime: {ve} para '{hora_str}'")  # Log detallado
                    return data.get('response', f'Hora inválida después de limpieza "{hora_str}". Usa HH:MM (ej. 12:00).')

                try:
                    mesas_disp = get_mesas_disponibles(str(fecha), str(hora))
                    if mesas_disp:
                        mesa_id = mesas_disp[0].id
                        is_valid, msg = validar_reserva(self.user_id, mesa_id, str(fecha), str(hora), num_comensales)
                        if is_valid:
                            reserva = Reserva(
                                usuario_id=self.user_id,
                                mesa_id=mesa_id,
                                fecha_reserva=fecha,
                                hora_reserva=hora,
                                num_comensales=num_comensales
                            )
                            db.session.add(reserva)
                            db.session.commit()

                            for plato_nombre in platos:
                                plato = Plato.query.filter_by(nombre=plato_nombre).first()
                                if plato:
                                    pedido = PedidoReserva(reserva_id=reserva.id, plato_id=plato.id, cantidad=1)
                                    db.session.add(pedido)
                            for bebida_nombre in bebidas:
                                bebida = Bebida.query.filter_by(nombre=bebida_nombre).first()
                                if bebida:
                                    pedido = PedidoReserva(reserva_id=reserva.id, bebida_id=bebida.id, cantidad=1)
                                    db.session.add(pedido)
                            db.session.commit()

                            enviar_confirmacion_reserva(reserva.id)
                            return data.get('response', f'Reserva #{reserva.id} confirmada para {fecha} a las {hora}.')
                        else:
                            return f"No se pudo reservar: {msg}"
                    else:
                        return data.get('response', 'No hay mesas disponibles.')
                except Exception as db_error:
                    import traceback
                    error_details = f"Error en base de datos o validación: {str(db_error)}\n{traceback.format_exc()}"
                    print(error_details)  # Log para depuración
                    return f"Error al procesar la reserva (posible problema con disponibilidad o base de datos): {str(db_error)}. Intenta con otra fecha/hora."
            else:
                # Para general, retornar la response del JSON
                return data.get('response', ollama_response or 'No pude generar respuesta.')
        except json.JSONDecodeError:
            # Fallback si no es JSON
            return ollama_response or 'Error en el procesamiento. Intenta de nuevo.'