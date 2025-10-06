from app import app, db
from models.user import User
from models.reservation import Mesa
from models.menu import Plato, Bebida
from werkzeug.security import generate_password_hash

with app.app_context():
    # Crear mesas (1 a 20)
    for i in range(1, 21):
        if not Mesa.query.filter_by(numero_mesa=i).first():
            mesa = Mesa(numero_mesa=i, capacidad=4, estado='disponible')
            db.session.add(mesa)

    # Crear platos (10 opciones)
    platos_data = [
        ('Ensalada fresca', 'entrada', 8.5),
        ('Sopa del día', 'entrada', 6.0),
        ('Carne asada', 'plato fuerte', 18.0),
        ('Pollo al horno', 'plato fuerte', 16.0),
        ('Pescado grillado', 'plato fuerte', 20.0),
        ('Pasta carbonara', 'plato fuerte', 14.0),
        ('Pizza margarita', 'plato fuerte', 12.0),
        ('Hamburguesa clásica', 'plato fuerte', 13.0),
        ('Tarta de manzana', 'postre', 5.0),
        ('Helado de vainilla', 'postre', 4.5)
    ]

    for nombre, categoria, precio in platos_data:
        if not Plato.query.filter_by(nombre=nombre).first():
            plato = Plato(nombre=nombre, categoria=categoria, precio=precio, disponible=True)
            db.session.add(plato)

    # Crear bebidas (7 opciones)
    bebidas_data = [
        ('Jugo de naranja', 'jugo', 3.5),
        ('Jugo de fresa', 'jugo', 3.5),
        ('Refresco de cola', 'refresco', 2.5),
        ('Refresco de limón', 'refresco', 2.5),
        ('Agua mineral', 'agua', 2.0),
        ('Cerveza local', 'cerveza', 4.0),
        ('Vino tinto', 'vino', 6.0)
    ]

    for nombre, tipo, precio in bebidas_data:
        if not Bebida.query.filter_by(nombre=nombre).first():
            bebida = Bebida(nombre=nombre, tipo=tipo, precio=precio, disponible=True)
            db.session.add(bebida)

    # Crear usuario admin de ejemplo (opcional)
    if not User.query.filter_by(email='admin@example.com').first():
        admin = User(nombre='Admin', email='admin@example.com', password_hash=generate_password_hash('admin123'))
        db.session.add(admin)

    db.session.commit()
    db.session.commit()
    print("Base de datos inicializada con éxito: 20 mesas, 10 platos, 7 bebidas y usuario admin (admin@example.com / admin123).")
