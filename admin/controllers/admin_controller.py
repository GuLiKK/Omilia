import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from utils.auth_utils import is_admin_or_moderator, is_admin
from marshmallow import ValidationError
from admin.schemas.admin_schemas import UserActionSchema, DemoteUserSchema, PromoteUserSchema
from admin.services.admin_service import (
    list_all_users,
    block_user as block_user_service,
    unblock_user as unblock_user_service,
    promote_user as promote_user_service,
    demote_user as demote_user_service
)

admin_bp = Blueprint("admin_bp", __name__)
logger = logging.getLogger(__name__)

@admin_bp.route("/admin/users", methods=["GET"])
@jwt_required()
@is_admin_or_moderator
def list_users():
    """
    Получить список всех пользователей
    ---
    description: Вывод списка всех пользователей (доступно для admin и moderator).
    tags:
      - Admin
    security:
      - bearerAuth: []
    responses:
      200:
        description: Список пользователей (JSON array)
        schema:
          type: array
          items:
            type: object
            properties:
              username:
                type: string
                example: "user_12345678"
                description: Имя пользователя
              role:
                type: string
                example: "user"
                description: Роль пользователя
              id:
                type: integer
                example: 1
                description: Идентификатор пользователя
      403:
        description: Недостаточно прав или пользователь заблокирован
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    logger.debug("Admin/moderator requested user list")
    users_data = list_all_users()
    return jsonify(users_data)

@admin_bp.route("/admin/block_user", methods=["POST"])
@jwt_required()
@is_admin_or_moderator
def block_user():
    """
    Заблокировать пользователя
    ---
    description: Заблокировать выбранного пользователя (admin или moderator).
    tags:
      - Admin
    security:
      - bearerAuth: []
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/UserActionModel'
    responses:
      200:
        description: Пользователь успешно заблокирован
        schema:
          $ref: '#/definitions/MessageResponse'
      400:
        description: Некорректные данные
        schema:
          $ref: '#/definitions/ErrorResponse'
      403:
        description: Недостаточно прав / пользователь заблокирован
        schema:
          $ref: '#/definitions/ErrorResponse'
      404:
        description: Пользователь не найден
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    logger.debug("Admin attempts to block user")
    try:
        data = UserActionSchema().load(request.json or {})
    except ValidationError as e:
        logger.debug(f"Block user validation error: {e.messages}")
        return jsonify(e.messages), 400

    user_id = data["user_id"]
    user_ = block_user_service(user_id)
    if not user_:
        logger.debug(f"User with id {user_id} not found for blocking")
        return jsonify({"error": "User not found"}), 404
    return jsonify({"message": f"User {user_id} blocked successfully"})

@admin_bp.route("/admin/unblock_user", methods=["POST"])
@jwt_required()
@is_admin_or_moderator
def unblock_user():
    """
    Разблокировать пользователя
    ---
    description: Разблокировать выбранного пользователя (admin или moderator).
    tags:
      - Admin
    security:
      - bearerAuth: []
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/UserActionModel'
    responses:
      200:
        description: Пользователь успешно разблокирован
        schema:
          $ref: '#/definitions/MessageResponse'
      400:
        description: Некорректные данные
        schema:
          $ref: '#/definitions/ErrorResponse'
      403:
        description: Недостаточно прав / пользователь заблокирован
        schema:
          $ref: '#/definitions/ErrorResponse'
      404:
        description: Пользователь не найден
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    logger.debug("Admin attempts to unblock user")
    try:
        data = UserActionSchema().load(request.json or {})
    except ValidationError as e:
        logger.debug(f"Unblock user validation error: {e.messages}")
        return jsonify(e.messages), 400

    user_id = data["user_id"]
    user_ = unblock_user_service(user_id)
    if not user_:
        logger.debug(f"User with id {user_id} not found for unblocking")
        return jsonify({"error": "User not found"}), 404
    return jsonify({"message": f"User {user_id} unblocked successfully"})

@admin_bp.route("/admin/promote", methods=["POST"])
@jwt_required()
@is_admin
def promote_user():
    """
    Повысить роль пользователя
    ---
    description: Повысить роль пользователя (доступно только admin).
    tags:
      - Admin
    security:
      - bearerAuth: []
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/DemoteOrPromoteUserModel'
    responses:
      200:
        description: Пользователь успешно повышен
        schema:
          $ref: '#/definitions/MessageResponse'
      400:
        description: Некорректные данные
        schema:
          $ref: '#/definitions/ErrorResponse'
      403:
        description: Нет прав или пользователь заблокирован
        schema:
          $ref: '#/definitions/ErrorResponse'
      404:
        description: Пользователь не найден
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    logger.debug("Admin attempts to promote user to admin/moderator")
    try:
        data = PromoteUserSchema().load(request.json or {})
    except ValidationError as e:
        logger.debug(f"Promote user validation error: {e.messages}")
        return jsonify(e.messages), 400

    user_id = data["user_id"]
    new_role = data["new_role"]
    user_ = promote_user_service(user_id, new_role)
    if not user_:
        logger.debug(f"User with id {user_id} not found for promotion")
        return jsonify({"error": "User not found"}), 404

    return jsonify({"message": f"User {user_id} is now an {new_role}"}), 200

@admin_bp.route("/admin/demote", methods=["POST"])
@jwt_required()
@is_admin
def demote_user():
    """
    Понизить роль пользователя
    ---
    description: Понизить роль пользователя (только для admin).
    tags:
      - Admin
    security:
      - bearerAuth: []
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/DemoteOrPromoteUserModel'
    responses:
      200:
        description: Роль пользователя успешно изменена
        schema:
          $ref: '#/definitions/MessageResponse'
      400:
        description: Некорректные данные
        schema:
          $ref: '#/definitions/ErrorResponse'
      403:
        description: Нет прав или пользователь заблокирован
        schema:
          $ref: '#/definitions/ErrorResponse'
      404:
        description: Пользователь не найден
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    logger.debug("Admin attempts to demote user")
    try:
        data = DemoteUserSchema().load(request.json or {})
    except ValidationError as e:
        logger.debug(f"Demote user validation error: {e.messages}")
        return jsonify(e.messages), 400

    user_id = data["user_id"]
    new_role = data["new_role"]
    user_ = demote_user_service(user_id, new_role)
    if not user_:
        logger.debug(f"User with id {user_id} not found for demotion")
        return jsonify({"error": "User not found"}), 404

    return jsonify({"message": f"User {user_id} role changed to {new_role}"}), 200
