from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    image_path = db.Column(db.String(255), nullable=False)
    dominant_emotion = db.Column(db.String(50), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    emotions = db.Column(db.Text, nullable=False)  # Хранение эмоций в JSON-формате

    user = db.relationship('User', backref=db.backref('results', lazy=True))