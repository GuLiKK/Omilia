import logging
import os
from flask import Blueprint, jsonify, request, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from schemas.room_schemas import JoinRoomSchema
from services.room_service import (
    join_room_service,
    leave_room_service,
    my_room_service,
    get_room_messages_service
)
from core.database import get_redis_client
from models.user import User

logger = logging.getLogger(__name__)
room_bp = Blueprint('room_bp', __name__)

def get_current_user():
    """
    Извлекает текущего пользователя (JWT), проверяет блокировку в Redis.
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
    
    # Проверка блокировки
    if r.get(f"user:{user_id}:blocked") == "1":
        abort(403, description="User is blocked")

    return user

@room_bp.route('/join_room', methods=['POST'])
@jwt_required()
def join_room():
    """
    Присоединение к комнате
    ---
    description: Войти в комнату нужного размера (room_size).
    tags:
      - Rooms
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
            room_size:
              type: integer
              example: 3
    responses:
      200:
        description: Успешное присоединение к существующей комнате
        schema:
          $ref: '#/definitions/MessageResponse'
      201:
        description: Создана новая комната
        schema:
          $ref: '#/definitions/MessageResponse'
      400:
        description: Пользователь уже в комнате
        schema:
          $ref: '#/definitions/ErrorResponse'
      403:
        description: Пользователь заблокирован
        schema:
          $ref: '#/definitions/ErrorResponse'
      404:
        description: Нет подходящей комнаты или пользователь не найден
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    logger.debug(f"Joining room (PID: {os.getpid()})")
    user_ = get_current_user()
    if not user_:
        logger.debug("User not found during join_room")
        return jsonify({"error": "User not found"}), 404

    try:
        data = JoinRoomSchema().load(request.json or {})
    except ValidationError as e:
        logger.debug(f"Join room validation failed: {e.messages}")
        return jsonify(e.messages), 400

    room_size = data['room_size']
    room_id, error, status_code = join_room_service(user_, room_size)
    if error:
        return jsonify({"error": error}), status_code

    if status_code == 200:
        return jsonify({"message": "Joined room successfully", "room_id": room_id}), 200
    elif status_code == 201:
        return jsonify({"message": "Created and joined new room", "room_id": room_id}), 201
    else:
        return jsonify({"error": "Unknown error"}), 500

@room_bp.route('/leave_room', methods=['POST'])
@jwt_required()
def leave_room():
    """
    Выход из комнаты
    ---
    description: Пользователь покидает комнату, если он в ней.
    tags:
      - Rooms
    security:
      - bearerAuth: []
    responses:
      200:
        description: Успешный выход из комнаты
        schema:
          $ref: '#/definitions/MessageResponse'
      400:
        description: Пользователь не в комнате
        schema:
          $ref: '#/definitions/ErrorResponse'
      403:
        description: Пользователь заблокирован
        schema:
          $ref: '#/definitions/ErrorResponse'
      404:
        description: Пользователь не найден
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    logger.debug("Leaving room")
    user_ = get_current_user()
    if not user_:
        logger.debug("User not found during leave_room")
        return jsonify({"error": "User not found"}), 404

    room_id, error, status_code = leave_room_service(user_)
    if error:
        return jsonify({"error": error}), status_code

    return jsonify({"message": "Left room successfully"}), status_code

@room_bp.route('/my_room', methods=['GET'])
@jwt_required()
def my_room():
    """
    Моя комната
    ---
    description: Узнать, в какой комнате находится пользователь (если вообще).
    tags:
      - Rooms
    security:
      - bearerAuth: []
    responses:
      200:
        description: Возвращает информацию о комнате
        schema:
          type: object
          properties:
            room_id:
              type: string
              nullable: true
              example: "room:3:123456"
            message:
              type: string
              example: "You are not in a room"
      403:
        description: Пользователь заблокирован
        schema:
          $ref: '#/definitions/ErrorResponse'
      404:
        description: Пользователь не найден
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    user_ = get_current_user()
    if not user_:
        return jsonify({"error": "User not found"}), 404

    room_id = my_room_service(user_)
    if not room_id:
        return jsonify({"room_id": None, "message": "You are not in a room"}), 200

    return jsonify({"room_id": room_id}), 200

@room_bp.route('/room_messages/<room_id>', methods=['GET'])
@jwt_required()
def room_messages(room_id):
    """
    Получение сообщений комнаты
    ---
    description: Получить все сообщения в заданной комнате (после времени входа пользователя).
    tags:
      - Rooms
    security:
      - bearerAuth: []
    parameters:
      - in: path
        name: room_id
        required: true
        schema:
          type: string
        description: Идентификатор комнаты (например, "room:3:123456")
    responses:
      200:
        description: Список сообщений в комнате
        schema:
          type: array
          items:
            type: object
            properties:
              user_id:
                type: string
                example: "user_12345678"
              content:
                type: string
                example: "Hello!"
              timestamp:
                type: string
                example: "2025-01-01T10:00:00+00:00"
      400:
        description: Пользователь не в комнате
        schema:
          $ref: '#/definitions/ErrorResponse'
      403:
        description: Пользователь заблокирован
        schema:
          $ref: '#/definitions/ErrorResponse'
      404:
        description: Пользователь не найден
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    logger.debug("Getting room messages")
    user_ = get_current_user()
    if not user_:
        logger.debug("User not found during room_messages")
        return jsonify({"error": "User not found"}), 404

    messages, error, status_code = get_room_messages_service(user_, room_id)
    if error:
        return jsonify({"error": error}), status_code

    return jsonify(messages), 200
