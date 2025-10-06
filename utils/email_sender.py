from flask import render_template, current_app, url_for
from flask_mail import Message
from models.reservation import Reserva
from models.menu import Plato, Bebida
from models.user import User

RESTAURANTE_NOMBRE = "Sabores y Raíces"
RESTAURANTE_DIRECCION = "Calle Falsa 123, Ciudad"
RESTAURANTE_TELEFONO = "+123 456 7890"
RESTAURANTE_EMAIL = "info@saboresyraices.com"

def enviar_confirmacion_reserva(reserva_id):
    """Envía email de confirmación al usuario y notificación al admin."""
    reserva = Reserva.query.get(reserva_id)
    if not reserva:
        return False, "Reserva no encontrada."

    usuario = User.query.get(reserva.usuario_id)
    mesa = reserva.mesa

    # Resumen del pedido
    pedidos = reserva.pedidos
    resumen_pedido = []
    for pedido in pedidos:
        if pedido.plato:
            plato = Plato.query.get(pedido.plato_id)
            resumen_pedido.append(f"{pedido.cantidad} x {plato.nombre} - ${plato.precio * pedido.cantidad:.2f}")
        elif pedido.bebida:
            bebida = Bebida.query.get(pedido.bebida_id)
            resumen_pedido.append(f"{pedido.cantidad} x {bebida.nombre} - ${bebida.precio * pedido.cantidad:.2f}")

    if not resumen_pedido:
        resumen_pedido = ["No se han agregado pedidos."]

    # Email al usuario
    msg_usuario = Message(
        subject=f"Confirmación de Reserva #{reserva.id} - {RESTAURANTE_NOMBRE}",
        recipients=[usuario.email],
        sender=current_app.config['MAIL_DEFAULT_SENDER']
    )
    mail = current_app.extensions['mail']
    msg_usuario.html = render_template(
        'emails/reserva_confirmacion_usuario.html',
        reserva=reserva,
        usuario=usuario,
        mesa=mesa,
        resumen_pedido=resumen_pedido,
        restaurante={
            'nombre': RESTAURANTE_NOMBRE,
            'direccion': RESTAURANTE_DIRECCION,
            'telefono': RESTAURANTE_TELEFONO,
            'email': RESTAURANTE_EMAIL
        },
        cancel_link=url_for('reservations.cancelar', reserva_id=reserva.id, _external=True)
    )
    mail.send(msg_usuario)

    # Email al admin
    msg_admin = Message(
        subject=f"Nueva Reserva #{reserva.id} - {RESTAURANTE_NOMBRE}",
        recipients=[RESTAURANTE_EMAIL],
        sender=current_app.config['MAIL_DEFAULT_SENDER']
    )
    mail = current_app.extensions['mail']
    msg_admin.html = render_template(
        'emails/reserva_notificacion_admin.html',
        reserva=reserva,
        usuario=usuario,
        mesa=mesa,
        resumen_pedido=resumen_pedido,
        restaurante={
            'nombre': RESTAURANTE_NOMBRE,
            'direccion': RESTAURANTE_DIRECCION,
            'telefono': RESTAURANTE_TELEFONO,
            'email': RESTAURANTE_EMAIL
        }
    )
    mail.send(msg_admin)

    return True, "Emails enviados exitosamente."

def enviar_recordatorio_reserva(reserva_id):
    """Envía recordatorio 24h antes de la reserva (puede usarse con scheduler)."""
    reserva = Reserva.query.get(reserva_id)
    if not reserva:
        return False

    usuario = User.query.get(reserva.usuario_id)
    mesa = reserva.mesa

    msg = Message(
        subject=f"Recordatorio: Tu reserva en {RESTAURANTE_NOMBRE}",
        recipients=[usuario.email],
        sender=current_app.config['MAIL_DEFAULT_SENDER']
    )
    msg.html = render_template(
        'emails/reserva_recordatorio.html',
        reserva=reserva,
        usuario=usuario,
        mesa=mesa,
        restaurante={
            'nombre': RESTAURANTE_NOMBRE,
            'direccion': RESTAURANTE_DIRECCION,
            'telefono': RESTAURANTE_TELEFONO
        }
    )
    mail.send(msg)

    return True