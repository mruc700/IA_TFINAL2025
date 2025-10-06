# Sistema de Chatbot para Reservas de Restaurante - Sabores y Raíces

Este proyecto implementa un sistema completo de reservas de restaurante con integración de chatbot IA usando Ollama (Llama 3) y bot de Telegram. Incluye autenticación, gestión de reservas, menú digital, notificaciones por email y más.

## Características

- **Autenticación segura**: Registro/login con Flask-Login y hashing bcrypt.
- **Sistema de reservas**: Selección de mesas, ver disponibilidad, prevención de dobles reservas.
- **Menú digital**: Visualización de platos/bebidas, carrito de pedidos asociado a reservas.
- **Calendario**: Visualización y gestión de reservas.
- **Notificaciones email**: Confirmaciones automáticas para usuario y admin con templates HTML.
- **Chatbot IA**: Procesamiento de lenguaje natural con Ollama para reservas y recomendaciones.
- **Bot de Telegram**: Comandos (/start, /reservar, etc.), botones inline, sincronización con BD.
- **Seguridad**: Rate limiting, validación de formularios, sanitización de inputs.

## Tecnologías

- Backend: Python 3.8+, Flask
- BD: SQLite con SQLAlchemy
- Autenticación: Flask-Login
- Email: Flask-Mail
- IA: Ollama (Llama 3)
- Telegram: python-telegram-bot
- Seguridad: Flask-Limiter, WTForms

## Estructura del Proyecto

```
restaurant-chatbot/
├── app.py                      # App Flask principal
├── config.py                   # Configuraciones
├── requirements.txt            # Dependencias
├── .env.example                # Variables de entorno (copiar a .env)
├── init_db.py                  # Script inicialización BD
├── models/                     # Modelos SQLAlchemy
│   ├── __init__.py
│   ├── database.py
│   ├── user.py
│   ├── reservation.py
│   └── menu.py
├── routes/                     # Rutas Flask
│   ├── __init__.py
│   ├── auth.py
│   ├── reservations.py
│   ├── menu.py
│   └── chatbot.py
├── chatbot/                    # Lógica chatbot IA
│   ├── __init__.py
│   ├── ollama_client.py
│   └── conversation.py
├── telegram_bot/               # Bot Telegram
│   ├── __init__.py
│   ├── bot.py
│   └── handlers.py
├── templates/                  # Plantillas HTML
│   ├── base.html
│   ├── login.html
│   ├── register.html          # Pendiente actualización
│   ├── dashboard.html
│   ├── reservations.html
│   ├── menu.html
│   ├── chatbot.html           # Pendiente
│   └── emails/                 # Templates email
│       ├── reserva_confirmacion_usuario.html
│       └── reserva_notificacion_admin.html
├── static/                     # Archivos estáticos
│   ├── css/
│   ├── js/
│   └── images/                 # Logo_SR.jpg
└── utils/                      # Utilidades
    ├── __init__.py
    ├── email_sender.py
    └── calendar_helper.py
```

## Instalación y Uso

### 1. Clonar y Configurar

```bash
git clone <repo-url>
cd restaurant-chatbot
cp .env.example .env
```

### 2. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar Variables de Entorno (.env)

- `SECRET_KEY`: Clave secreta Flask (genera una segura).
- `DATABASE_URL`: `sqlite:///restaurant.db` (o PostgreSQL/MySQL).
- **Email** (Gmail ejemplo):
  - `MAIL_SERVER=smtp.gmail.com`
  - `MAIL_PORT=587`
  - `MAIL_USE_TLS=true`
  - `MAIL_USERNAME=tu_email@gmail.com`
  - `MAIL_PASSWORD=tu_app_password` (usa contraseña de app en Gmail).
- `TELEGRAM_BOT_TOKEN`: Token del bot de Telegram (crea en @BotFather).
- `OLLAMA_HOST=http://localhost:11434` (instala Ollama localmente).

### 4. Inicializar Base de Datos

```bash
python init_db.py
```

Esto crea las tablas y pobla datos de ejemplo (20 mesas, 10 platos, 7 bebidas).

### 5. Ejecutar Aplicación Web

```bash
python app.py
```

Accede en `http://localhost:5000`. Regístrate/login para usar el sistema.

### 6. Configurar Bot de Telegram

1. Crea un bot en Telegram con @BotFather y obtén el token.
2. Actualiza `TELEGRAM_BOT_TOKEN` en .env.
3. Ejecuta el bot:

```bash
python telegram_bot/bot.py
```

Comandos: /start, /reservar, /mis_reservas, /cancelar, /menu. Soporta conversación natural con IA.

### 7. Configurar Ollama

1. Instala Ollama: https://ollama.ai
2. Descarga modelo: `ollama pull llama3`
3. Asegura que corra en `localhost:11434`.

### 8. Configurar Email

Para Gmail, habilita "Contraseñas de app" en tu cuenta Google y usa una para `MAIL_PASSWORD`.

## Documentación API REST

El sistema usa rutas Flask como API básica:

- **Autenticación**:
  - POST /login: {email, password} → Sesión
  - POST /registro: {nombre, email, telefono, password} → Usuario nuevo

- **Reservas**:
  - GET /reservas: Lista reservas usuario
  - POST /reservas/nueva: {fecha_reserva, hora_reserva, num_comensales, mesa_id, notas} → Nueva reserva
  - GET /api/disponibilidad?fecha=YYYY-MM-DD&hora=HH:MM → Mesas disponibles (JSON)
  - GET /reservas/cancelar/<id> → Cancelar reserva

- **Menú**:
  - GET /menu: Lista platos/bebidas
  - POST /menu/agregar/<id>: {tipo, cantidad} → Agregar carrito
  - GET /menu/carrito: Ver carrito
  - POST /menu/asociar_reserva/<reserva_id>: Asocia carrito a reserva

- **Chatbot**:
  - GET /chatbot: Interfaz web
  - POST /chatbot/converse: {message} → Respuesta IA (JSON)

Usa herramientas como Postman para probar.

## Instrucciones para Bot de Telegram

1. Ejecuta `python telegram_bot/bot.py`.
2. En Telegram, busca tu bot y envía /start.
3. Usa comandos o botones para navegar.
4. Para conversación IA, usa /chatbot o mensajes libres.
5. El bot sincroniza con la BD SQLite (mismo usuario via email/telegram_id).

Nota: Para producción, usa webhook en lugar de polling y base de datos robusta.

## Testing - Ejemplos de Flujos

### 1. Flujo Completo de Reserva (Web)

1. Registro: POST /registro con datos válidos → Usuario creado.
2. Login: POST /login → Sesión activa.
3. Nueva reserva: GET /reservas/nueva → Formulario.
   - Selecciona fecha/hora → API disponibilidad devuelve mesas JSON.
   - POST datos → Reserva creada, emails enviados (ver logs).
4. Ver reservas: GET /reservas → Lista con botones cancelar/pedir menú.
5. Cancelar: GET /reservas/cancelar/1 → Estado 'cancelada'.

**Caso de Error**: Intentar reserva en fecha pasada → Validación falla, flash error.

### 2. Flujo Menú y Pedido

1. GET /menu → Lista items.
2. POST /menu/agregar/1 {tipo: 'plato', cantidad: 2} → Carrito en sesión.
3. GET /menu/carrito → Muestra total.
4. POST /menu/asociar_reserva/1 → Pedidos guardados en BD.

**Error**: Carrito vacío al asociar → Flash info.

### 3. Interacciones Chatbot (Web)

1. GET /chatbot → Interfaz.
2. POST /chatbot/converse {message: "Quiero reservar para 4 el viernes"} → Respuesta IA, posible acción JSON para reserva.

**Ejemplo Respuesta**: "Perfecto, ¿para qué hora? Disponible 12:00 o 19:00."

### 4. Comandos Telegram

- /start → Menú botones.
- /reservar → Pide email → Flujo reserva.
- /menu → Lista menú con botones.
- /mis_reservas → Lista reservas (si usuario asociado).
- Mensaje libre: "Recomienda vegetariano" → Usa Ollama para respuesta.

**Error**: Usuario no registrado → Pide email.

**Caso Telegram Reserva**:
1. /reservar → Email → Fecha → Hora → Confirma y crea reserva, envía email.

### 5. Notificaciones Email

Al crear reserva, envía:
- Usuario: Confirmación con detalles, link cancelar.
- Admin: Notificación nueva reserva.

**Error**: Config SMTP inválida → Logs error, reserva creada pero sin email.

Para pruebas completas, ejecuta app.py y bot.py, usa browser/Telegram.

## Notas Adicionales

- **Seguridad**: Implementado rate limiting global. Para producción, agrega CSRF en forms (WTForms lo maneja), valida/sanitiza inputs en chatbot (ver conversation.py).
- **Características Deseables**: Admin panel, recordatorios (usa APScheduler), multi-idioma (Flask-Babel) pendientes para v2.
- **Producción**: Usa Gunicorn/NGINX, PostgreSQL, HTTPS, env vars seguras.
- **Ollama**: Requiere GPU para rendimiento óptimo.

¡El sistema está listo para uso! Contribuciones bienvenidas.