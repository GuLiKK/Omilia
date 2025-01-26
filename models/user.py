from core.database import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    telegram_id = db.Column(db.String(50), unique=True, nullable=True)
    username = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'user', 'admin', ...

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
