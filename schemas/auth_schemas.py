from marshmallow import Schema, fields, ValidationError, validates_schema
from models.user import User

class RegisterSchema(Schema):
    login = fields.Str(required=True)
    password = fields.Str(required=True)

    @validates_schema
    def validate_user(self, data, **kwargs):
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
