import re
from marshmallow import Schema, fields, ValidationError, validates, validates_schema
from models.user import User

class RegisterSchema(Schema):
    login = fields.Str(required=True)
    password = fields.Str(required=True)

    @validates("password")
    def validate_password(self, value):
        """
        Собираем все ошибки, если они есть.
        """
        errors = []
        if len(value) < 8:
            errors.append("Password must be at least 8 characters long.")
        if not re.search(r'[A-Z]', value):
            errors.append("Password must contain at least one uppercase letter.")
        if not re.search(r'\d', value):
            errors.append("Password must contain at least one digit.")
        if not re.search(r'[^a-zA-Z0-9]', value):
            errors.append("Password must contain at least one special symbol.")
        if errors:
            raise ValidationError(errors)

    @validates_schema
    def validate_user(self, data, **kwargs):
        """
        Проверка, что логин не занят.
        """
        if User.query.filter_by(login=data['login']).first():
            raise ValidationError("User with this login already exists", field_name='login')

class LoginSchema(Schema):
    login = fields.Str()
    password = fields.Str()
    telegram_id = fields.Str()

class LinkTelegramSchema(Schema):
    telegram_id = fields.Str(required=True)

class ChangeUsernameSchema(Schema):
    username = fields.Str(required=True)
