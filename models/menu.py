from .database import db

class Plato(db.Model):
    __tablename__ = 'platos'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    categoria = db.Column(db.String(50))
    precio = db.Column(db.Float, nullable=False)
    disponible = db.Column(db.Boolean, default=True)

    # Relationships
    pedidos_plato = db.relationship('PedidoReserva', back_populates='plato', foreign_keys='PedidoReserva.plato_id', lazy=True)

class Bebida(db.Model):
    __tablename__ = 'bebidas'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(50))
    precio = db.Column(db.Float, nullable=False)
    disponible = db.Column(db.Boolean, default=True)

    # Relationships
    pedidos_bebida = db.relationship('PedidoReserva', back_populates='bebida', foreign_keys='PedidoReserva.bebida_id', lazy=True)