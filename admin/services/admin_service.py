import logging
from models.user import User
from core.database import db, get_redis_client
from services.room_service import leave_room_service

logger = logging.getLogger(__name__)

def list_all_users():
    """
    Возвращает список всех пользователей в формате list[dict].
    """
    users = User.query.all()
    return [{"id": u.id, "role": u.role, "username": u.username} for u in users]

def block_user(user_id: int):
    """
    Блокирует пользователя (устанавливает ключ в Redis).
    Если пользователь находится в комнате, удаляем его оттуда.
    Возвращает объект пользователя или None, если не найден.
    """
    user = User.query.get(user_id)
    if not user:
        return None

    r = get_redis_client()
    if r is None:
        raise RuntimeError("Cannot connect to Redis")
    
    # Ставим флаг блокировки в Redis
    r.set(f"user:{user_id}:blocked", "1")
    logger.info(f"User {user_id} blocked successfully (redis)")

    # Проверяем, не находится ли пользователь в комнате
    room_id = r.hget(f"user:{user.id}", "room")
    if room_id:
        # Пользователь в комнате -> выкидываем
        logger.info(f"User {user_id} is in room {room_id}, forcing leave_room")
        _, _, _ = leave_room_service(user)  # Возвращаем значение, игнорируя room_id, error, status_code

    return user

def unblock_user(user_id: int):
    """
    Снимает блокировку с пользователя (удаляет ключ в Redis).
    Возвращает объект пользователя или None, если не найден.
    """
    user = User.query.get(user_id)
    if not user:
        return None
    r = get_redis_client()
    if r is None:
        raise RuntimeError("Cannot connect to Redis")
    
    r.delete(f"user:{user_id}:blocked")
    logger.info(f"User {user_id} unblocked successfully")
    return user

def promote_user(user_id: int, new_role: str):
    """
    Повышает пользователя до роли 'admin' или 'moderator'.
    Возвращает объект пользователя или None, если не найден.
    """
    user = User.query.get(user_id)
    if not user:
        return None
    user.role = new_role
    db.session.commit()
    logger.info(f"User {user_id} promoted to {new_role}")
    return user

def demote_user(user_id: int, new_role: str):
    """
    Демотировать пользователя до `new_role`.
    Предполагаем, что new_role может быть "user" или "moderator".
    Если user не найден - возвращаем None.
    """
    user = User.query.get(user_id)
    if not user:
        return None

    user.role = new_role
    db.session.commit()
    logger.info(f"User {user_id} demoted to {new_role}")
    return user
