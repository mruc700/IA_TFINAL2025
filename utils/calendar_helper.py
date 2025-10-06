from datetime import datetime, time
from models.reservation import Reserva, Mesa
from models.database import db

# Bloques horarios disponibles (ejemplo: almuerzo y cena)
HORARIOS_DISPONIBLES = [
    ('12:00', 'Almuerzo (12:00 - 14:00)'),
    ('19:00', 'Cena (19:00 - 22:00)')
]

def get_horarios_disponibles():
    """Retorna los bloques horarios disponibles."""
    return HORARIOS_DISPONIBLES

def is_mesa_disponible(mesa_id, fecha_reserva, hora_reserva):
    """Verifica si una mesa está disponible para una fecha y hora específicas."""
    # Convertir fecha y hora a datetime para comparación
    fecha = datetime.strptime(fecha_reserva, '%Y-%m-%d').date()
    hora = datetime.strptime(hora_reserva, '%H:%M').time()
    
    # Buscar reservas existentes para esa mesa en la misma fecha y hora (mismo bloque)
    reservas_existentes = Reserva.query.filter_by(
        mesa_id=mesa_id,
        fecha_reserva=fecha,
        hora_reserva=hora,
        estado='confirmada'
    ).all()
    
    return len(reservas_existentes) == 0

def get_mesas_disponibles(fecha_reserva, hora_reserva):
    """Obtiene las mesas disponibles para una fecha y hora."""
    mesas_disponibles = []
    mesas = Mesa.query.filter_by(estado='disponible').all()
    
    for mesa in mesas:
        if is_mesa_disponible(mesa.id, fecha_reserva, hora_reserva):
            mesas_disponibles.append(mesa)
    
    return mesas_disponibles

def validar_reserva(usuario_id, mesa_id, fecha_reserva, hora_reserva, num_comensales):
    """Valida si se puede crear una reserva (disponibilidad y capacidad)."""
    mesa = Mesa.query.get(mesa_id)
    if not mesa:
        return False, "Mesa no encontrada."
    
    if mesa.capacidad < num_comensales:
        return False, "La mesa no tiene capacidad suficiente."
    
    if not is_mesa_disponible(mesa_id, fecha_reserva, hora_reserva):
        return False, "La mesa no está disponible en ese horario."
    
    # Verificar si el usuario ya tiene una reserva en ese horario
    reserva_existente = Reserva.query.filter_by(
        usuario_id=usuario_id,
        fecha_reserva=fecha_reserva,
        hora_reserva=hora_reserva,
        estado='confirmada'
    ).first()
    
    if reserva_existente:
        return False, "Ya tienes una reserva en ese horario."
    
    return True, "Reserva válida."

def get_reservas_usuario(usuario_id):
    """Obtiene el historial de reservas de un usuario."""
    reservas = Reserva.query.filter_by(usuario_id=usuario_id).order_by(Reserva.fecha_creacion.desc()).all()
    return reservas

def get_calendario_reservas(mes=None, año=None):
    """Obtiene reservas para visualización mensual del calendario."""
    if mes and año:
        fecha_inicio = datetime(año, mes, 1)
        fecha_fin = (fecha_inicio.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    else:
        fecha_inicio = datetime.now().replace(day=1)
        fecha_fin = (fecha_inicio.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    
    reservas = Reserva.query.filter(
        Reserva.fecha_reserva >= fecha_inicio.date(),
        Reserva.fecha_reserva <= fecha_fin.date(),
        Reserva.estado == 'confirmada'
    ).all()
    
    return reservas