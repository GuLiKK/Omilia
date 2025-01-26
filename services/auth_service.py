import logging
from datetime import timedelta
from flask_jwt_extended import create_access_token, create_refresh_token
from core.database import db
from models.user import User
from controllers.utils import generate_username

logger = logging.getLogger(__name__)

def register_user(login: str, password: str):
    """
    Создаёт нового пользователя. Возвращает (user, error),
    где user = объект User, или None если произошла ошибка;
    error = текст ошибки (str) или None, если всё ок.
    """
    # Проверка, нет ли уже пользователя с таким логином
    if User.query.filter_by(login=login).first():
        return None, "User with this login already exists"

    # Генерируем username, пока не найдём свободный
    username = generate_username()
    while User.query.filter_by(username=username).first():
        username = generate_username()

    user = User(login=login, username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    logger.info(f"User registered successfully: {login}")
    return user, None

def login_user(login: str = None,
               password: str = None,
               telegram_id: str = None,
               remember: bool = False):
    """
    Логика входа пользователя.
    Возвращает (user, error, access_token, refresh_token).
    Если error не None, значит что-то пошло не так.
    """
    # Попытка входа по логину+паролю
    if login and password:
        user = User.query.filter_by(login=login).first()
        if not user or not user.check_password(password):
            return None, "Invalid login or password", None, None

        # Настраиваем срок действия
        access_expires = timedelta(minutes=15)
        refresh_expires = timedelta(hours=1)

        if remember:
            # "Remember me" -> пусть refresh-токен живёт 30 дней
            refresh_expires = timedelta(days=30)

        access_token = create_access_token(identity=str(user.id),
                                           expires_delta=access_expires)
        refresh_token = create_refresh_token(identity=user.id,
                                             expires_delta=refresh_expires)

        return user, None, access_token, refresh_token

    # Попытка входа по Telegram ID
    if telegram_id:
        user = User.query.filter_by(telegram_id=telegram_id).first()
        if not user:
            return None, (
                "No user with this telegram_id. "
                "Please login with login/password and link your telegram_id."
            ), None, None

        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=user.id)
        return user, None, access_token, refresh_token

    # Иначе данные некорректны
    return None, "Invalid credentials", None, None

def link_telegram_id(user: User, telegram_id: str):
    """
    Привязывает к user указанный telegram_id.
    Возвращает (user, error).
    """
    # Проверим, не занят ли уже телеграм другими
    if User.query.filter_by(telegram_id=telegram_id).first():
        return None, "This telegram_id is already linked to another account"

    user.telegram_id = telegram_id
    db.session.commit()
    logger.info(f"Telegram ID {telegram_id} linked to user {user.login}")
    return user, None

def change_username(user: User, new_username: str):
    """
    Меняет username пользователя.
    Возвращает (user, error).
    """
    if User.query.filter_by(username=new_username).first():
        return None, "Username is already taken"

    user.username = new_username
    db.session.commit()
    logger.info(f"Username changed successfully for user {user.login}")
    return user, None
