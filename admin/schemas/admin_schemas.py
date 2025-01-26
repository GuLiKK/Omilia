from marshmallow import Schema, fields, validate

class UserActionSchema(Schema):
    user_id = fields.Int(required=True, description="ID пользователя")

class DemoteUserSchema(Schema):
    user_id = fields.Int(required=True, description="ID пользователя")
    new_role = fields.Str(required=True,
                          validate=validate.OneOf(["user","moderator"]),
                          description="Роль, до которой понижаем (user/moderator)")

class PromoteUserSchema(Schema):
    user_id = fields.Int(required=True, description="ID пользователя")
    new_role = fields.Str(required=True,
                          validate=validate.OneOf(["moderator", "admin"]),
                          description="Новая роль (moderator или admin)")
