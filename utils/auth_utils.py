from functools import wraps
from flask_jwt_extended import get_jwt_identity
from models.user import User
from flask import jsonify

def is_admin(fn):
    """
    Декоратор для проверки, является ли пользователь администратором.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user or user.role != "admin":
            return jsonify({"error": "Access denied"}), 403
        return fn(*args, **kwargs)
    return wrapper

def is_admin_or_moderator(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user or user.role not in ("admin", "moderator"):
            return jsonify({"error": "Access denied"}), 403
        return fn(*args, **kwargs)
    return wrapper

