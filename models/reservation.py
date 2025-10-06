from .database import db
from datetime import datetime

class Mesa(db.Model):
    __tablename__ = 'mesas'

    id = db.Column(db.Integer, primary_key=True)
    numero_mesa = db.Column(db.Integer, unique=True, nullable=False)
    capacidad = db.Column(db.Integer, default=4)
    estado = db.Column(db.String(20), default='disponible')

    # Relationships
    reservas = db.relationship('Reserva', backref='mesa', lazy=True)

class Reserva(db.Model):
    __tablename__ = 'reservas'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    mesa_id = db.Column(db.Integer, db.ForeignKey('mesas.id'), nullable=False)
    fecha_reserva = db.Column(db.Date, nullable=False)
    hora_reserva = db.Column(db.Time, nullable=False)
    num_comensales = db.Column(db.Integer, nullable=False)
    estado = db.Column(db.String(20), default='confirmada')
    notas = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    pedidos = db.relationship('PedidoReserva', back_populates='reserva', lazy=True, cascade='all, delete-orphan')

class PedidoReserva(db.Model):
    __tablename__ = 'pedidos_reserva'

    id = db.Column(db.Integer, primary_key=True)
    reserva_id = db.Column(db.Integer, db.ForeignKey('reservas.id'), nullable=False)
    plato_id = db.Column(db.Integer, db.ForeignKey('platos.id'), nullable=True)
    bebida_id = db.Column(db.Integer, db.ForeignKey('bebidas.id'), nullable=True)
    cantidad = db.Column(db.Integer, default=1)

    # Relationships
    reserva = db.relationship('Reserva', back_populates='pedidos')
    plato = db.relationship('Plato', back_populates='pedidos_plato', foreign_keys=[plato_id])
    bebida = db.relationship('Bebida', back_populates='pedidos_bebida', foreign_keys=[bebida_id])