import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError
from schemas.complaint_schemas import CreateComplaintSchema
from services.complaint_service import create_complaint
from controllers.auth_controller import get_current_user

logger = logging.getLogger(__name__)

complaint_bp = Blueprint("complaint_bp", __name__)

@complaint_bp.route("/complaints", methods=["POST"])
@jwt_required()
def submit_complaint():
    """
    Отправить жалобу
    ---
    description: Создать жалобу на пользователя (произвольная причина).
    tags:
      - Complaints
    security:
      - bearerAuth: []
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/CreateComplaintModel'
    responses:
      201:
        description: Жалоба успешно создана
        schema:
          $ref: '#/definitions/MessageResponse'
      400:
        description: Некорректные данные
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
    user_ = get_current_user()
    if not user_:
        logger.debug("User not found while trying to submit complaint")
        return jsonify({"error": "User not found"}), 404

    try:
        data = CreateComplaintSchema().load(request.json or {})
    except ValidationError as e:
        logger.debug(f"Complaint validation failed: {e.messages}")
        return jsonify(e.messages), 400

    complaint_id, error = create_complaint(
        reporter_id=user_.id,
        target_user_id=data["target_user_id"],
        message_id=data.get("message_id"),
        reason=data.get("reason", "")
    )
    if error:
        return jsonify({"error": error}), 400

    logger.info(f"User {user_.id} submitted complaint ID={complaint_id}")
    return jsonify({"message": "Complaint submitted", "complaint_id": complaint_id}), 201
