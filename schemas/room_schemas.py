from marshmallow import Schema, fields, ValidationError, validates_schema

class JoinRoomSchema(Schema):
    room_size = fields.Int(required=True)

    @validates_schema
    def validate_room_size(self, data, **kwargs):
        size = data["room_size"]
        if size < 2 or size > 10:
            raise ValidationError("room_size must be from 2 to 10", field_name='room_size')
