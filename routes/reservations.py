from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models.database import db
from models.reservation import Reserva, Mesa
from utils.calendar_helper import get_horarios_disponibles, get_mesas_disponibles, validar_reserva
from utils.email_sender import enviar_confirmacion_reserva
from datetime import datetime

reservations_bp = Blueprint('reservations', __name__, template_folder='templates')

@reservations_bp.route('/reservas')
@login_required
def index():
    """Lista las reservas del usuario actual."""
    reservas = Reserva.query.filter_by(usuario_id=current_user.id).order_by(Reserva.fecha_reserva.desc(), Reserva.hora_reserva).all()
    return render_template('reservations.html', reservas=reservas)

@reservations_bp.route('/reservas/nueva', methods=['GET', 'POST'])
@login_required
def nueva():
    """Formulario para crear una nueva reserva."""
    if request.method == 'POST':
        fecha_reserva = request.form['fecha_reserva']
        hora_reserva = request.form['hora_reserva']
        num_comensales = int(request.form['num_comensales'])
        mesa_id = int(request.form['mesa_id'])
        notas = request.form.get('notas', '')

        # Validar reserva
        is_valid, message = validar_reserva(current_user.id, mesa_id, fecha_reserva, hora_reserva, num_comensales)
        if is_valid:
            # Crear reserva
            reserva = Reserva(
                usuario_id=current_user.id,
                mesa_id=mesa_id,
                fecha_reserva=datetime.strptime(fecha_reserva, '%Y-%m-%d').date(),
                hora_reserva=datetime.strptime(hora_reserva, '%H:%M').time(),
                num_comensales=num_comensales,
                notas=notas
            )
            db.session.add(reserva)
            db.session.commit()
            
            # Enviar emails de confirmación
            success, msg = enviar_confirmacion_reserva(reserva.id)
            if success:
                flash('Reserva creada y confirmación enviada exitosamente', 'success')
            else:
                flash(f'Reserva creada, pero error en email: {msg}', 'warning')
            
            return redirect(url_for('reservations.index'))
        else:
            flash(f'Error al crear reserva: {message}', 'error')

    # GET: mostrar formulario
    fecha = request.args.get('fecha', datetime.now().strftime('%Y-%m-%d'))
    hora = request.args.get('hora', '12:00')
    horarios = get_horarios_disponibles()
    mesas_disp = get_mesas_disponibles(fecha, hora)
    return render_template('nueva_reserva.html', horarios=horarios, mesas_disp=mesas_disp, fecha=fecha, hora=hora)

@reservations_bp.route('/api/disponibilidad')
@login_required
def disponibilidad():
    """API para obtener mesas disponibles por fecha y hora (AJAX)."""
    fecha = request.args.get('fecha')
    hora = request.args.get('hora')
    if not fecha or not hora:
        return jsonify({'error': 'Faltan parámetros'}), 400

    mesas_disp = get_mesas_disponibles(fecha, hora)
    mesas_list = [{'id': m.id, 'numero': m.numero_mesa, 'capacidad': m.capacidad} for m in mesas_disp]
    return jsonify({'mesas': mesas_list})

@reservations_bp.route('/reservas/cancelar/<int:reserva_id>')
@login_required
def cancelar(reserva_id):
    """Cancelar una reserva del usuario."""
    reserva = Reserva.query.filter_by(id=reserva_id, usuario_id=current_user.id).first()
    if reserva:
        reserva.estado = 'cancelada'
        db.session.commit()
        flash('Reserva cancelada exitosamente', 'success')
    else:
        flash('Reserva no encontrada', 'error')
    return redirect(url_for('reservations.index'))