import os
import redis, time
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO

db = SQLAlchemy()
jwt = JWTManager()
socketio = SocketIO()
_redis_client = None

def init_db(app):
    """
    Инициализация БД (SQLAlchemy).
    """
    db.init_app(app)
    with app.app_context():
        db.create_all()

def init_jwt(app):
    """
    Настройка JWT.
    """
    # Включаем хранение refresh-токена в cookie
    app.config['JWT_TOKEN_LOCATION'] = ['cookies', 'headers']
    # Access-токен можно возвращать в теле ответа, refresh-токен в куки
    # Для реального remember-me нужно, чтобы refresh-токен жил дольше
    app.config['JWT_HEADER_TYPE'] = ''
    app.config['JWT_COOKIE_SECURE'] = False   # Для HTTPS включить True
    app.config['JWT_COOKIE_SAMESITE'] = 'Strict'  # Или 'None'/'Lax'
    app.config['JWT_COOKIE_CSRF_PROTECT'] = False
    app.config['JWT_SESSION_COOKIE'] = False  # Если не хотим session-based

    # Применяем настройки
    jwt.init_app(app)

def init_socketio(app):
    """
    Инициализация SocketIO.
    """
    socketio.init_app(app, cors_allowed_origins="*")
    return socketio

def get_redis_client():
    """
    Возвращает подключение к Redis, 
    при необходимости создаёт новое (хуета крч).
    """
    global _redis_client
    if _redis_client is not None:
        # Уже есть подключение
        return _redis_client

    host = os.environ.get("REDIS_HOST", "127.0.0.1")
    port = int(os.environ.get("REDIS_PORT", "6379"))
    password = os.environ.get("REDIS_PASSWORD", "")
    db_ = int(os.environ.get("REDIS_DB", 0))
    retries = 5

    for attempt in range(1, retries + 1):
        try:
            r = redis.Redis(
                host=host,
                port=port,
                db=db_,
                password=password,
                decode_responses=True,
                socket_timeout=5
            )
            r.ping()  # проверка соединения
            print(f"Connected to Redis at {host}:{port} on attempt {attempt}")
            _redis_client = r
            return _redis_client
        except redis.ConnectionError as e:
            print(f"Failed to connect to Redis on attempt {attempt}: {e}")
            time.sleep(2)

    print("Failed to connect to Redis after retries.")
    # Если все 5 попыток упали, остаёмся с None
    return None

# def init_redis():
#     global redis_client
#     host = os.environ.get("REDIS_HOST", "127.0.0.1")
#     port = int(os.environ.get("REDIS_PORT", 6379))
#     db_ = int(os.environ.get("REDIS_DB", 0))
#     try:
#         redis_client = redis.Redis(host=host, port=port, db=db_, decode_responses=True, socket_timeout=5)
#         redis_client.ping()
#     except redis.ConnectionError as e:
#         print(f"Failed to connect to Redis: {e}")
#         redis_client = None
