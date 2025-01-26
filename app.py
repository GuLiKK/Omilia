import os
import sys
from flask import Flask
from flasgger import Swagger
from config.loader import load_config_yml
from core.logging_setup import setup_logging
from core.database import init_db, init_jwt, init_socketio #, init_redis
from controllers.auth_controller import auth_bp
from controllers.room_controller import room_bp
from admin.controllers.admin_controller import admin_bp

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

    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec",
                "route": "/apispec.json",
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/apidocs",
    }

    # Дополняем шаблон определением UserActionModel:
    swagger_template = {
        "info": {
            "title": "Omilia",
            "description": "Открытый API для анонимного чата",
            "version": "0.2.0"
        },
        "basePath": "/",
        "produces": ["application/json"],
        "consumes": ["application/json"],
        "definitions": {
            "RegisterModel": {
                "type": "object",
                "properties": {
                    "login": {"type": "string", "example": "my_login"},
                    "password": {"type": "string", "example": "my_password"}
                }
            },
            "LoginModel": {
                "type": "object",
                "properties": {
                    "login": {"type": "string"},
                    "password": {"type": "string"},
                    "telegram_id": {"type": "string"}
                }
            },
            "UserActionModel": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "integer", "example": 123}
                }
            },
            "DemoteOrPromoteUserModel": {
                "type": "object",
                "properties": {
                    "new_role": {
                        "type": "string",
                        "enum": ["user", "moderator"],
                        "example": "moderator"
                    },
                    "user_id": {
                        "type": "integer",
                        "example": 123
                    }
                }
            }
        },
        "securityDefinitions": {
            "bearerAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "Authorization",
                "description": "Введите <токен>"
            }
        }
    }


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

if __name__ == "__main__":
    app.logger.info(f"Omilia launched PID={os.getpid()}")
    socketio.run(app, debug=False, use_reloader=False)
