from apscheduler.schedulers.background import BackgroundScheduler
from models.database import db
from models.reservation import Reserva
from utils.email_sender import enviar_recordatorio_reserva
from datetime import datetime, timedelta
import time

def init_scheduler(app):
    """Inicializa el scheduler para recordatorios de reservas."""
    scheduler = BackgroundScheduler()
    scheduler.start()
    
    def send_reminders():
        """Función para enviar recordatorios 24h antes de reservas."""
        tomorrow = datetime.now().date() + timedelta(days=1)
        reservas = Reserva.query.filter(
            Reserva.fecha_reserva == tomorrow,
            Reserva.estado == 'confirmada'
        ).all()
        
        for reserva in reservas:
            # Enviar recordatorio al usuario
            enviar_recordatorio_reserva(reserva.id)
            print(f"Recordatorio enviado para reserva {reserva.id}")
    
    # Programar job diario a las 9 AM
    scheduler.add_job(
        send_reminders,
        'cron',
        hour=9,
        minute=0,
        id='daily_reminders'
    )
    
    app.scheduler = scheduler  # Guardar en app para shutdown

def shutdown_scheduler(app):
    """Detiene el scheduler al cerrar la app."""
    if hasattr(app, 'scheduler'):
        app.scheduler.shutdown()