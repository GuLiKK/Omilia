import logging
from datetime import datetime
from core.database import get_redis_client

logger = logging.getLogger(__name__)

def create_complaint(reporter_id: int, target_user_id: int, message_id: str = None, reason: str = ""):
    """
    Создаёт новую жалобу в Redis. Возвращает (complaint_id, error).
    """
    r = get_redis_client()
    if r is None:
        return None, "Cannot connect to Redis"

    try:
        # complaint_id auto-increment
        complaint_id = r.incr("complaint_id_counter")
        complaint_key = f"complaint:{complaint_id}"

        complaint_data = {
            "reporter_id": str(reporter_id),
            "target_user_id": str(target_user_id),
            "message_id": message_id or "",
            "reason": reason or "",
            "created_at": datetime.utcnow().isoformat()
        }

        # Сохраняем в Redis Hash:
        r.hset(complaint_key, mapping=complaint_data)
        # Добавим в множество/список всех жалоб:
        r.sadd("complaints:all", complaint_id)

        return complaint_id, None
    except Exception as e:
        logger.exception("Failed to create complaint in Redis")
        return None, "Internal server error"

def list_complaints():
    """
    Возвращает список всех жалоб.
    """
    r = get_redis_client()
    if r is None:
        return []

    try:
        all_ids = r.smembers("complaints:all")
        results = []
        for cid in all_ids:
            complaint_key = f"complaint:{cid}"
            data = r.hgetall(complaint_key)
            if data:
                data["complaint_id"] = int(cid)
                results.append(data)
        # Можно сортировать по complaint_id (для удобства)
        results.sort(key=lambda c: c["complaint_id"])
        return results
    except Exception as e:
        logger.exception("Failed to list complaints")
        return []

def remove_complaint(complaint_id: int):
    """
    Удаляет жалобу из Redis. Возвращает (removed_bool, error_string|None).
    """
    r = get_redis_client()
    if r is None:
        return False, "Cannot connect to Redis"

    complaint_key = f"complaint:{complaint_id}"
    if not r.exists(complaint_key):
        return False, "Complaint not found"

    try:
        r.delete(complaint_key)
        r.srem("complaints:all", complaint_id)
        return True, None
    except Exception as e:
        logger.exception("Failed to remove complaint")
        return False, "Internal server error"
