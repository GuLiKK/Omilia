import logging
from flask import request
from flask_socketio import emit, join_room
from datetime import datetime, timezone
from flask_jwt_extended import decode_token
from flask_jwt_extended.exceptions import JWTExtendedException
from .database import socketio, get_redis_client
from models.user import User

connected_users = {}  # user_id -> sid
logger = logging.getLogger(__name__)

@socketio.on('connect')
def handle_connect():
    token = request.args.get('token')
    if not token:
        logger.debug("No token provided on Socket.IO connect -> rejecting")
        return False  # нет токена — не пускаем

    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            logger.debug("No user_id in token payload -> reject")
            return False
        user = User.query.get(user_id)
        if not user:
            logger.debug("User not found in DB -> reject")
            return False

        connected_users[user_id] = request.sid
        # --- ДОБАВКА: смотрим, в какой room_id числится пользователь в Redis ---
        r = get_redis_client()
        room_id = r.hget(f"user:{user.id}", "room")  # например, "room:3:12345"
        if room_id:
            join_room(room_id)  # <-- теперь этот сокет реально зашёл в room_id
            logger.info(f"User {user_id} joined Socket.IO room {room_id} (sid={request.sid})")

        logger.info(f"User {user.login} connected via SocketIO (sid={request.sid})")
        return True

    except JWTExtendedException:
        logger.error("Invalid token on Socket.IO connect")
        return False
    
@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    user_id_to_remove = None

    for uid, stored_sid in list(connected_users.items()):
        if stored_sid == sid:
            user_id_to_remove = uid
            break

    if user_id_to_remove:
        del connected_users[user_id_to_remove]
        logger.info(f"Socket disconnected (sid={sid}), user_id={user_id_to_remove}")

@socketio.on('send_message')
def handle_send_message(data):
    logger.debug("SocketIO send_message event")

    sid = request.sid
    user_id = None
    for uid, stored_sid in connected_users.items():
        if stored_sid == sid:
            user_id = uid
            break

    if user_id is None:
        logger.error("User not authenticated in send_message")
        emit('error', {"error": "Not authenticated"})
        return

    user = User.query.get(user_id)
    if not user:
        logger.error("User not found in DB in send_message")
        emit('error', {"error": "User not found"})
        return
    
    r = get_redis_client()
    if r is None:
        logger.error("Cannot connect to Redis in send_message")
        emit('error', {"error": "Internal server error"})
        return
    
    room_id = r.hget(f"user:{user.id}", "room")
    if not room_id:
        logger.error("User tried to send message without being in a room")
        emit('error', {"error": "You are not in a room"})
        return

    message = data.get('message')
    if not message or not isinstance(message, str) or message.strip() == '':
        logger.error("No valid message provided in send_message event")
        emit('error', {"error": "No valid message provided"})
        return

    timestamp = datetime.now(timezone.utc).isoformat()
    r.rpush(f"{room_id}:messages", f"{user.username}:{message}:{timestamp}")

    logger.info(f"User {user.login} sent message to room {room_id}")
    emit('new_message', {"user_id": user.username, "message": message, "timestamp": timestamp}, room=room_id)
