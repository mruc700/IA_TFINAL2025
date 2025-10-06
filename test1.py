from app import app
from models.user import User
from models.database import db

with app.app_context():
    # Verificar si ya existe por email
    existing = User.query.filter_by(email='max.reyes@gmail.com').first()
    if existing:
        print("Usuario ya existe con ID:", existing.id)
    else:
        user = User(
            nombre='MAXIMILIANO ULU',
            email='max.reyes@gmail.com',
            telefono='60690727'
        )
        user.set_password('ingreso12345')  # Hashea la contraseña con bcrypt
        db.session.add(user)
        db.session.commit()
        print("Usuario insertado exitosamente con ID:", user.id)
        print("Email: max.reyes@gmail.com")
        print("Password: ingreso12345 (hasheada en BD)")