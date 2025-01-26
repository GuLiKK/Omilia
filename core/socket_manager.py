import logging
from flask import request
from flask_socketio import emit
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
        logger.warning("No token provided on connect")
        return False

    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            logger.warning("Invalid token payload on connect")
            return False

        user = User.query.get(user_id)
        if not user:
            logger.warning("User not found for given token on connect")
            return False

        connected_users[user_id] = request.sid
        logger.info(f"User {user.login} connected via SocketIO (sid={request.sid})")
        return True
    except JWTExtendedException:
        logger.warning("Invalid token on connect")
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
        logger.debug(f"Socket disconnected (sid={sid}), user_id={user_id_to_remove}")

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
        logger.warning("User not authenticated in send_message")
        emit('error', {"error": "Not authenticated"})
        return

    user = User.query.get(user_id)
    if not user:
        logger.warning("User not found in send_message")
        emit('error', {"error": "User not found"})
        return
    
    r = get_redis_client
    if r is None:
        raise RuntimeError("Cannot connect to Redis")
    
    room_id = r.hget(f"user:{user.id}", "room")
    if not room_id:
        logger.warning("User tried to send message without being in a room")
        emit('error', {"error": "You are not in a room"})
        return

    message = data.get('message')
    if not message or not isinstance(message, str) or message.strip() == '':
        logger.warning("No valid message provided in send_message event")
        emit('error', {"error": "No valid message provided"})
        return

    timestamp = datetime.now(timezone.utc).isoformat()
    
    r = get_redis_client
    if r is None:
        raise RuntimeError("Cannot connect to Redis")
    r.rpush(f"{room_id}:messages", f"{user.username}:{message}:{timestamp}")

    logger.info(f"User {user.login} sent message to room {room_id}")
    emit('new_message', {"user_id": user.username, "message": message, "timestamp": timestamp}, room=room_id)
