import logging
from flask import Blueprint, jsonify, request, make_response, abort
from flask_jwt_extended import (
    create_access_token, jwt_required,
    get_jwt_identity, set_refresh_cookies,
    unset_jwt_cookies
)
from marshmallow import ValidationError
from datetime import timedelta
from schemas.auth_schemas import RegisterSchema, LoginSchema, LinkTelegramSchema, ChangeUsernameSchema
from services.auth_service import (
    register_user,
    login_user,
    link_telegram_id,
    change_username as change_username_service
)
from services.room_service import leave_room_service
from core.database import get_redis_client
from models.user import User

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth_bp', __name__)

def get_current_user():
    """
    Извлекает текущего пользователя на основе токена JWT (access или refresh).
    Дополнительно проверяет в Redis, нет ли флага блокировки user:{user_id}:blocked.
    Если заблокирован — прерываем запрос (abort(403)).
    """
    user_id = get_jwt_identity()
    if user_id is None:
        return None

    user = User.query.get(user_id)
    if not user:
        return None
    r = get_redis_client()
    if r is None:
        raise RuntimeError("Cannot connect to Redis")
    
    # Проверка блокировки через Redis
    if r.get(f"user:{user_id}:blocked") == "1":
        abort(403, description="User is blocked")

    return user

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Регистрация пользователя
    ---
    description: Зарегистрировать пользователя.
    tags:
      - Auth
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/RegisterModel'
    responses:
      201:
        description: Успешная регистрация
      400:
        description: Ошибка валидации или уже существует пользователь
      403:
        description: Пользователь заблокирован (редко бывает для регистрации, но оставляем для единообразия)
    """
    logger.info("Attempting user registration")
    try:
        data = RegisterSchema().load(request.json or {})
    except ValidationError as e:
        logger.info(f"Registration validation failed: {e.messages}")
        return jsonify(e.messages), 400

    login_ = data['login']
    password = data['password']

    user, error = register_user(login_, password)
    if error:
        return jsonify({"error": error}), 400

    return jsonify({"message": "Registration successful", "username": user.username}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Вход (логин)
    ---
    description: Войти в аккаунт пользователя.
    tags:
      - Auth
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/LoginModel'
    responses:
      200:
        description: Успешный вход (возвращаются access_token и refresh_token)
      400:
        description: Неверные данные
      403:
        description: Пользователь заблокирован
      404:
        description: Не найден пользователь
    """
    logger.info("User login attempt")
    try:
        data = LoginSchema().load(request.json or {})
    except ValidationError as e:
        logger.info(f"Login validation failed: {e.messages}")
        return jsonify(e.messages), 400

    login_ = data.get('login')
    password = data.get('password')
    telegram_id = data.get('telegram_id')

    # Параметр ?remember=1 в query (GET-параметрах)
    remember = (request.args.get("remember", "0") == "1")

    user, error, access_token, refresh_token = login_user(
        login=login_,
        password=password,
        telegram_id=telegram_id,
        remember=remember
    )
    if error:
        # Если ошибка про telegram_id, отдадим 404 (нет такого пользователя)
        status_code = 404 if "telegram_id" in error else 400
        return jsonify({"error": error}), status_code

    resp = make_response(jsonify({
        "message": ("Login successful"
                    if (login_ and password) else "Login successful via telegram_id"),
        "access_token": access_token
    }))
    # Устанавливаем refresh-токен в HttpOnly-cookie
    set_refresh_cookies(resp, refresh_token)
    return resp, 200

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Обновление access-токена
    ---
    description: Обновление access-токена с помощью refresh-токена.
    tags:
      - Auth
    security:
      - bearerAuth: []
    responses:
      200:
        description: Возвращает новый access-токен
      401:
        description: Недействительный refresh-токен
      403:
        description: Пользователь заблокирован
      404:
        description: Пользователь не найден
    """
    logger.debug("Attempting to refresh token")
    user_id = get_jwt_identity()
    if not user_id:
        return jsonify({"error": "User not found"}), 404

    new_access_token = create_access_token(
        identity=str(user_id),
        expires_delta=timedelta(minutes=15)
    )
    logger.debug(f"Access token refreshed for user_id: {user_id}")

    resp = make_response(jsonify({"access_token": new_access_token}))
    return resp, 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required(refresh=True)
def logout():
    """
    Выход (логаут)
    ---
    description: Выйти из аккаунта пользователя, пользователь также покидает комнату, если он в ней (сброс Refresh-токена).
    tags:
      - Auth
    consumes:
      - application/json
    responses:
      200:
        description: Успешный выход
      403:
        description: Пользователь заблокирован
    """
    logger.debug("Logging out")

    user_ = get_current_user()
    if user_:
        # Если пользователь в комнате - выкинем
        _, _, _ = leave_room_service(user_)

    resp = make_response(jsonify({"message": "Logout successful"}))
    unset_jwt_cookies(resp)
    return resp, 200

@auth_bp.route('/link_telegram', methods=['POST'])
@jwt_required()
def link_telegram():
    """
    Привязка Telegram ID
    ---
    description: Привязать Telegram_id при входе в аккаунт в Telegram.
    tags:
      - Auth
    security:
      - bearerAuth: []
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            telegram_id:
              type: string
              example: "my_new_telegram_id"
    responses:
      200:
        description: telegram_id привязан
      400:
        description: Ошибка валидации
      403:
        description: Пользователь заблокирован
      404:
        description: Нет пользователя
    """
    logger.debug("Linking telegram_id")
    user_ = get_current_user()
    if not user_:
        logger.debug("User not found during link_telegram")
        return jsonify({"error": "User not found"}), 404

    try:
        schema = LinkTelegramSchema().load(request.json or {})
    except ValidationError as e:
        logger.debug(f"Link telegram validation failed: {e.messages}")
        return jsonify(e.messages), 400

    telegram_id = schema['telegram_id']
    user, error = link_telegram_id(user_, telegram_id)
    if error:
        return jsonify({"error": error}), 400

    return jsonify({"message": "Telegram ID linked successfully"}), 200

@auth_bp.route('/change_username', methods=['POST'])
@jwt_required()
def change_username():
    """
    Смена юзернейма
    ---
    description: Сменить имя пользователя.
    tags:
      - Auth
    security:
      - bearerAuth: []
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
              example: "my_new_username"
    responses:
      200:
        description: username изменён
      400:
        description: Некорректные данные
      403:
        description: Пользователь заблокирован
      404:
        description: Пользователь не найден
    """
    logger.debug("Changing username")
    user_ = get_current_user()
    if not user_:
        logger.debug("User not found during change_username")
        return jsonify({"error": "User not found"}), 404

    try:
        schema = ChangeUsernameSchema().load(request.json or {})
    except ValidationError as e:
        logger.debug(f"Change username validation failed: {e.messages}")
        return jsonify(e.messages), 400

    new_username = schema['username']
    user, error = change_username_service(user_, new_username)
    if error:
        return jsonify({"error": error}), 400

    return jsonify({"message": "Username changed successfully"}), 200
