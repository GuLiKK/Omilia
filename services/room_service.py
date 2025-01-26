import logging
import random
from datetime import datetime
from core.database import get_redis_client
from models.user import User

logger = logging.getLogger(__name__)

def notify_room_users(room_id: str, message: str):
    """
    Записывает уведомление всем пользователям комнаты (в список notifications в Redis).
    """
    try:

        r = get_redis_client()
        if r is None:
            raise RuntimeError("Cannot connect to Redis")
        
        users = r.smembers(f"{room_id}:users")
        logger.debug(f"Notifying users in room {room_id}: {users}")
        for uid in users:
            r.rpush(f"{room_id}:notifications", message)
    except Exception as e:
        logger.exception(f"Failed to notify users in room {room_id}: {e}")

def join_room_service(user: User, room_size: int):
    """
    Пользователь пытается присоединиться к комнате размера room_size.
    Возвращает (room_id, error, status_code).
      - room_id: str или None
      - error: str или None
      - status_code: int (200, 201, 400, 500 и т.д.)
    """

    r = get_redis_client()
    if r is None:
        raise RuntimeError("Cannot connect to Redis")

    # Проверим, не в комнате ли уже пользователь
    user_room = r.hget(f"user:{user.id}", "room")
    if user_room:
        logger.debug(f"User {user.login} is already in a room")
        return None, "You are already in a room", 400

    room_set_key = f"rooms:{room_size}"
    try:
        available_rooms = r.smembers(room_set_key)
    except Exception as e:
        logger.exception(f"Failed to get available_rooms: {e}")
        return None, "Internal server error", 500

    chosen_room = None
    for r_id in available_rooms:
        try:
            curr_str = r.hget(r_id, "current_users")
            max_str = r.hget(r_id, "max_users")
            if not curr_str or not max_str:
                continue
            current_users = int(curr_str)
            max_users = int(max_str)
            if current_users < max_users:
                chosen_room = r_id
                break
        except Exception as e:
            logger.exception(f"Failed to parse room info for {r_id}: {e}")
            continue

    if chosen_room:
        # Присоединяемся к существующей комнате
        try:
            r.hincrby(chosen_room, "current_users", 1)
            r.hset(f"user:{user.id}", "room", chosen_room)
            r.sadd(f"{chosen_room}:users", user.id)
            r.hset(f"user:{user.id}", "joined_at", datetime.now().isoformat())

            notify_room_users(chosen_room, f"User {user.username} has joined the room.")
            logger.info(f"User {user.login} joined room {chosen_room}")
            return chosen_room, None, 200
        except Exception as e:
            logger.exception(f"Failed to join existing room {chosen_room}: {e}")
            return None, "Internal server error", 500
    else:
        # Создаём новую комнату
        try:
            room_id = f"room:{room_size}:{random.randint(100000,999999)}"
            r.hset(room_id, "max_users", room_size)
            r.hset(room_id, "current_users", 1)
            r.hset(f"user:{user.id}", "room", room_id)
            r.sadd(f"{room_id}:users", user.id)
            r.hset(f"user:{user.id}", "joined_at", datetime.now().isoformat())

            r.sadd(room_set_key, room_id)
            notify_room_users(room_id, f"User {user.username} created and joined the room.")
            logger.info(f"User {user.login} created & joined room {room_id}")
            return room_id, None, 201
        except Exception as e:
            logger.exception(f"Failed to create and join new room: {e}")
            return None, "Internal server error", 500

def leave_room_service(user: User):
    """
    Пользователь выходит из комнаты. 
    Возвращает (room_id, error, status_code).
    """

    r = get_redis_client()
    if r is None:
        raise RuntimeError("Cannot connect to Redis")
    
    room_id = r.hget(f"user:{user.id}", "room")
    if not room_id:
        logger.debug(f"User {user.login} is not in any room")
        return None, "You are not in a room", 400

    try:
        r.hincrby(room_id, "current_users", -1)
        r.srem(f"{room_id}:users", user.id)
        r.hdel(f"user:{user.id}", "room")
        r.hdel(f"user:{user.id}", "joined_at")

        notify_room_users(room_id, f"User {user.username} has left the room.")
        logger.info(f"User {user.login} left room {room_id}")

        # Если в комнате никого не осталось — удалить
        if int(r.hget(room_id, "current_users")) == 0:
            _, size_str, _ = room_id.split(":")
            r.delete(room_id)
            r.delete(f"{room_id}:users")
            r.delete(f"{room_id}:messages")
            r.srem(f"rooms:{size_str}", room_id)
            logger.info(f"Room {room_id} deleted because it became empty")

        return room_id, None, 200
    except Exception as e:
        logger.exception(f"Failed to leave room {room_id}: {e}")
        return None, "Internal server error", 500

def my_room_service(user: User):
    """
    Возвращает ID комнаты, в которой находится пользователь, или None.
    """

    r = get_redis_client()
    if r is None:
        raise RuntimeError("Cannot connect to Redis")
    
    return r.hget(f"user:{user.id}", "room")

def get_room_messages_service(user: User, room_id: str):
    """
    Возвращает (list_of_messages, error, status_code).
    Только сообщения, написанные после того, как пользователь вошёл.
    """

    r = get_redis_client()
    if r is None:
        raise RuntimeError("Cannot connect to Redis")
    
    joined_at = r.hget(f"user:{user.id}", "joined_at")
    if not joined_at:
        logger.debug(f"User {user.login} has not joined room {room_id}")
        return None, "You have not joined this room", 400

    try:
        joined_time = datetime.fromisoformat(joined_at)
        messages = r.lrange(f"{room_id}:messages", 0, -1)
        formatted_messages = []

        for msg in messages:
            parts = msg.split(":")
            if len(parts) >= 3:
                sender_username, content, ts = parts[0], parts[1], ":".join(parts[2:])
                try:
                    msg_time = datetime.fromisoformat(ts)
                    # Берём только те, что после времени входа
                    if msg_time >= joined_time:
                        formatted_messages.append({
                            "user_id": sender_username,
                            "content": content,
                            "timestamp": ts
                        })
                except ValueError:
                    logger.debug(f"Invalid timestamp format in message: {msg}")
                    continue

        logger.info(f"Retrieved {len(formatted_messages)} messages in room {room_id} for user {user.login}")
        return formatted_messages, None, 200
    except Exception as e:
        logger.exception(f"Failed to get room messages for {room_id}: {e}")
        return None, "Internal server error", 500
