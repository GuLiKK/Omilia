swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/apispec.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs",
}

swagger_template = {
    "info": {
        "title": "Omilia",
        "description": "Открытый API для анонимного чата",
        "version": "0.3.0"
    },
    "basePath": "/",
    "produces": ["application/json"],
    "consumes": ["application/json"],

    "definitions": {
        "RegisterModel": {
            "type": "object",
            "properties": {
                "login": {"type": "string", "example": "my_login"},
                "password": {"type": "string", "example": "my_password"}
            }
        },
        "LoginModel": {
            "type": "object",
            "properties": {
                "login": {"type": "string", "example": "my_login"},
                "password": {"type": "string", "example": "my_password"},
                "telegram_id": {"type": "string", "example": "my_telegram_id"}
            }
        },
        "UserActionModel": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer", "example": 123}
            }
        },
        "DemoteOrPromoteUserModel": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "integer",
                    "example": 123
                },
                "new_role": {
                    "type": "string",
                    "enum": ["user", "moderator", "admin"],
                    "example": "moderator"
                }
            }
        },
        "ErrorResponse": {
            "type": "object",
            "properties": {
                "error": {"type": "string", "example": "Some error message"}
            }
        },
        "MessageResponse": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "example": "Some success message"}
            }
        },
        "CreateComplaintModel": {
            "type": "object",
            "properties": {
                "target_user_id": {
                    "type": "integer",
                    "example": 123
                },
                "message_id": {
                    "type": "string",
                    "example": "msg_12345"
                },
                "reason": {
                    "type": "string",
                    "example": "Spam or offensive content"
                }
            }
        },
        "ComplaintModel": {
            "type": "object",
            "properties": {
                "complaint_id": {"type": "integer", "example": 1},
                "reporter_id": {"type": "string", "example": "10"},
                "target_user_id": {"type": "string", "example": "20"},
                "message_id": {"type": "string", "example": "msg_12345"},
                "reason": {"type": "string", "example": "Spam or offensive content"},
                "created_at": {"type": "string", "example": "2025-01-01T10:00:00"}
            }
        }
    },

    "securityDefinitions": {
        "bearerAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "Введите *только* сам JWT-токен"
        }
    }
}
