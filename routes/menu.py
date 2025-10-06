from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import login_required, current_user
from models.database import db
from models.menu import Plato, Bebida
from models.reservation import PedidoReserva, Reserva
from datetime import datetime

menu_bp = Blueprint('menu', __name__, template_folder='templates')

@menu_bp.route('/menu')
@login_required
def index():
    """Visualización del menú digital."""
    platos = Plato.query.filter_by(disponible=True).all()
    bebidas = Bebida.query.filter_by(disponible=True).all()
    conteo_carrito = len(session.get('carrito', []))
    return render_template('menu.html', platos=platos, bebidas=bebidas, conteo_carrito=conteo_carrito)

@menu_bp.route('/menu/agregar/<int:item_id>', methods=['POST'])
@login_required
def agregar_carrito(item_id):
    """Agregar item al carrito de sesión."""
    tipo = request.form['tipo']  # 'plato' or 'bebida'
    cantidad = int(request.form['cantidad'])
    
    if 'carrito' not in session:
        session['carrito'] = []
    
    item = {'id': item_id, 'tipo': tipo, 'cantidad': cantidad}
    
    # Verificar si ya existe en carrito
    for i, cart_item in enumerate(session['carrito']):
        if cart_item['id'] == item_id and cart_item['tipo'] == tipo:
            session['carrito'][i]['cantidad'] += cantidad
            flash('Cantidad actualizada en el carrito', 'success')
            session.modified = True
            return redirect(url_for('menu.index'))
    
    session['carrito'].append(item)
    session.modified = True
    flash('Item agregado al carrito', 'success')
    return redirect(url_for('menu.index'))

@menu_bp.route('/menu/carrito')
@login_required
def carrito():
    """Visualización del carrito de pedidos."""
    pending_reserva_id = session.get('pending_reserva_id')
    if 'carrito' not in session or not session['carrito']:
        flash('El carrito está vacío', 'info')
        return render_template('carrito.html', total=0, items=[], pending_reserva_id=pending_reserva_id)
    
    items = []
    total = 0
    
    for item in session['carrito']:
        if item['tipo'] == 'plato':
            plato = Plato.query.get(item['id'])
            if plato:
                subtotal = plato.precio * item['cantidad']
                total += subtotal
                items.append({
                    'nombre': plato.nombre,
                    'precio': plato.precio,
                    'cantidad': item['cantidad'],
                    'subtotal': subtotal,
                    'tipo': 'Plato',
                    'item_id': item['id'],
                    'item_tipo': item['tipo']
                })
        elif item['tipo'] == 'bebida':
            bebida = Bebida.query.get(item['id'])
            if bebida:
                subtotal = bebida.precio * item['cantidad']
                total += subtotal
                items.append({
                    'nombre': bebida.nombre,
                    'precio': bebida.precio,
                    'cantidad': item['cantidad'],
                    'subtotal': subtotal,
                    'tipo': 'Bebida',
                    'item_id': item['id'],
                    'item_tipo': item['tipo']
                })
    
    return render_template('carrito.html', items=items, total=total, pending_reserva_id=pending_reserva_id)

@menu_bp.route('/menu/carrito/eliminar/<int:item_id>/<string:tipo>', methods=['POST'])
@login_required
def eliminar_carrito(item_id, tipo):
    """Eliminar item del carrito."""
    if 'carrito' in session:
        session['carrito'] = [item for item in session['carrito'] if not (item['id'] == item_id and item['tipo'] == tipo)]
        session.modified = True
        flash('Item eliminado del carrito', 'success')
    return redirect(url_for('menu.carrito'))

@menu_bp.route('/menu/asociar_reserva/<int:reserva_id>', methods=['GET', 'POST'])
@login_required
def asociar_reserva(reserva_id):
    """Asociar carrito con una reserva existente."""
    reserva = Reserva.query.filter_by(id=reserva_id, usuario_id=current_user.id).first()
    if not reserva:
        flash('Reserva no encontrada', 'error')
        return redirect(url_for('reservations.index'))
    
    if request.method == 'GET':
        session['pending_reserva_id'] = reserva_id
        session.modified = True
        return redirect(url_for('menu.carrito'))
    
    # POST
    if 'carrito' not in session or not session['carrito']:
        flash('El carrito está vacío', 'info')
        return redirect(url_for('menu.carrito'))
    
    for item in session['carrito']:
        pedido = PedidoReserva(
            reserva_id=reserva.id,
            plato_id=item['id'] if item['tipo'] == 'plato' else None,
            bebida_id=item['id'] if item['tipo'] == 'bebida' else None,
            cantidad=item['cantidad']
        )
        db.session.add(pedido)
    
    db.session.commit()
    del session['carrito']
    session.modified = True
    if 'pending_reserva_id' in session and session['pending_reserva_id'] == reserva_id:
        del session['pending_reserva_id']
        session.modified = True
    flash('Pedidos asociados a la reserva exitosamente', 'success')
    return redirect(url_for('reservations.index'))

@menu_bp.route('/api/menu/<tipo>')
def api_menu(tipo):
    """API para obtener menú por tipo (platos o bebidas)."""
    if tipo == 'platos':
        items = [{'id': p.id, 'nombre': p.nombre, 'descripcion': p.descripcion, 'precio': p.precio} for p in Plato.query.filter_by(disponible=True).all()]
    elif tipo == 'bebidas':
        items = [{'id': b.id, 'nombre': b.nombre, 'precio': b.precio} for b in Bebida.query.filter_by(disponible=True).all()]
    else:
        return jsonify({'error': 'Tipo inválido'}), 400
    
    return jsonify({'items': items})