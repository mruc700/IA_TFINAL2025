from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models.database import db
from models.user import User
from models.reservation import Reserva
from models.menu import Plato, Bebida
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__, template_folder='templates', url_prefix='/admin')

# Simple admin check - assume admin emails
ADMIN_EMAILS = ['admin@restaurant.com', 'encargado@saboresyraices.com']  # Configurable

def is_admin():
    return current_user.is_authenticated and current_user.email in ADMIN_EMAILS

@admin_bp.route('/')
@login_required
def index():
    if not is_admin():
        flash('Acceso denegado. Solo para administradores.', 'error')
        return redirect(url_for('dashboard'))
    
    # Estadísticas básicas
    total_usuarios = User.query.count()
    total_reservas = Reserva.query.count()
    reservas_hoy = Reserva.query.filter(
        Reserva.fecha_reserva == datetime.now().date(),
        Reserva.estado == 'confirmada'
    ).count()
    reservas_futuras = Reserva.query.filter(
        Reserva.fecha_reserva > datetime.now().date(),
        Reserva.estado == 'confirmada'
    ).count()
    platos_disponibles = Plato.query.filter_by(disponible=True).count()
    bebidas_disponibles = Bebida.query.filter_by(disponible=True).count()
    
    # Reservas recientes (últimos 7 días)
    reservas_recientes = Reserva.query.filter(
        Reserva.fecha_creacion >= datetime.now() - timedelta(days=7)
    ).order_by(Reserva.fecha_creacion.desc()).limit(10).all()
    
    return render_template('admin.html', 
                         total_usuarios=total_usuarios,
                         total_reservas=total_reservas,
                         reservas_hoy=reservas_hoy,
                         reservas_futuras=reservas_futuras,
                         platos_disponibles=platos_disponibles,
                         bebidas_disponibles=bebidas_disponibles,
                         reservas_recientes=reservas_recientes)

@admin_bp.route('/usuarios')
@login_required
def usuarios():
    if not is_admin():
        flash('Acceso denegado.', 'error')
        return redirect(url_for('dashboard'))
    
    usuarios = User.query.order_by(User.fecha_registro.desc()).all()
    return render_template('admin_usuarios.html', usuarios=usuarios)

@admin_bp.route('/reservas')
@login_required
def reservas():
    if not is_admin():
        flash('Acceso denegado.', 'error')
        return redirect(url_for('dashboard'))
    
    reservas = Reserva.query.order_by(Reserva.fecha_reserva.desc(), Reserva.hora_reserva).all()
    return render_template('admin_reservas.html', reservas=reservas)

@admin_bp.route('/menu')
@login_required
def menu_admin():
    if not is_admin():
        flash('Acceso denegado.', 'error')
        return redirect(url_for('dashboard'))
    
    platos = Plato.query.all()
    bebidas = Bebida.query.all()
    return render_template('admin_menu.html', platos=platos, bebidas=bebidas)

@admin_bp.route('/cancelar_reserva/<int:reserva_id>', methods=['POST'])
@login_required
def cancelar_reserva_admin(reserva_id):
    if not is_admin():
        flash('Acceso denegado.', 'error')
        return redirect(url_for('admin.reservas'))
    
    reserva = Reserva.query.get_or_404(reserva_id)
    reserva.estado = 'cancelada'
    db.session.commit()
    flash('Reserva cancelada por admin.', 'success')
    return redirect(url_for('admin.reservas'))