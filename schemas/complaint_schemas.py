from marshmallow import Schema, fields

class CreateComplaintSchema(Schema):
    target_user_id = fields.Int(required=True, description="ID пользователя, на кого жалуются")
    message_id = fields.Str(required=False, allow_none=True, description="ID сообщения или иной идентификатор")
    reason = fields.Str(required=False, allow_none=True, description="Причина жалобы")
