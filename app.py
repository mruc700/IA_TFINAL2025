from flask import Flask, render_template, redirect, url_for, flash
from flask_login import LoginManager, current_user
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config
from models.database import db
from routes.auth import auth_bp
from routes.reservations import reservations_bp
from routes.menu import menu_bp
from routes.chatbot import chatbot_bp
from routes.admin import admin_bp

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'

mail = Mail(app)

# Rate limiting
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

from models.user import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(reservations_bp)
app.register_blueprint(menu_bp)
app.register_blueprint(chatbot_bp)
app.register_blueprint(admin_bp)

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('auth.login'))

@app.route('/admin')
def admin_access():
    if current_user.is_authenticated:
        return redirect(url_for('admin.index'))
    return redirect(url_for('auth.login'))

@app.route('/dashboard')
def dashboard():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    return render_template('dashboard.html', nombre=current_user.nombre)

@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in ['es', 'en']:
        session['lang'] = lang
    return redirect(request.referrer or url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    # Inicializar scheduler para recordatorios
    from utils.reminder_scheduler import init_scheduler, shutdown_scheduler
    init_scheduler(app)
    
    try:
        app.run(debug=True)
    finally:
        shutdown_scheduler(app)