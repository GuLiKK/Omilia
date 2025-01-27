import os
from flask import Flask
from flasgger import Swagger
from config.loader import load_config_yml
from config.swagger import swagger_config, swagger_template
from core.logging_setup import setup_logging
from core.database import init_db, init_jwt, init_socketio #, init_redis
from controllers.auth_controller import auth_bp
from controllers.room_controller import room_bp
from admin.controllers.admin_controller import admin_bp
import core.socket_manager

def create_app():
    load_config_yml()  # Ставим env переменные

    # Проверка переменных окружения
    required_env_vars = ["REDIS_HOST", "REDIS_PORT", "REDIS_PASSWORD", "REDIS_DB", "SECRET_KEY", "JWT_SECRET_KEY"]
    for var in required_env_vars:
        if var not in os.environ:
            raise EnvironmentError(f"Environment variable {var} is not set")

    logger = setup_logging()  # Настраиваем логирование

    app = Flask(__name__)

    SECRET_KEY = os.environ.get("SECRET_KEY")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    BASE_DIR = os.environ.get("BASE_DIR", os.getcwd())

    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'chat.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY

    # Инициируем всё
    init_db(app)
    init_jwt(app)
    # init_redis()  # Инициализация Redis до импорта Blueprint

    swagger = Swagger(
        app,
        config=swagger_config,
        template=swagger_template
    )

    # Регистрируем Blueprint'ы
    app.register_blueprint(auth_bp, url_prefix='/')
    app.register_blueprint(room_bp, url_prefix='/')
    app.register_blueprint(admin_bp, url_prefix='/')

    return app

app = create_app()
socketio = init_socketio(app)

@app.errorhandler(RuntimeError)
def handle_runtime_error(e):
    """
    Глобальный обработчик RuntimeError
    """
    app.logger.error(f"RuntimeError: {str(e)}")
    return {"error": "Internal server error"}, 500

if __name__ == "__main__":
    app.logger.info(f"Omilia launched PID={os.getpid()}")
    socketio.run(app, debug=False, use_reloader=False)
