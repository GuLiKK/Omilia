import random

def generate_username():
    """
    Генерирует уникальный username,
    пока не найдёт незанятый в базе.
    """
    return f"user_{random.randint(10000000, 99999999)}"
