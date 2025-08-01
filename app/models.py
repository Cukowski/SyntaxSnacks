from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    preferred_languages = db.Column(db.String(256), default="Python,JavaScript")  # comma-separated
    streak = db.Column(db.Integer, default=0)
    last_active = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_lang_list(self):
        return [l.strip() for l in self.preferred_languages.split(",") if l.strip()]

class Challenge(db.Model):
    __tablename__ = "challenges"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    solution = db.Column(db.Text, nullable=False)
    hints = db.Column(db.Text, nullable=True)  # JSON list if multiple
    language = db.Column(db.String(50), nullable=False)
    topic = db.Column(db.String(80), nullable=True)
    difficulty = db.Column(db.String(30), default="easy")  # easy/medium/hard
    reference_url = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_hints(self):
        try:
            return json.loads(self.hints) if self.hints else []
        except:
            return []

class UserProgress(db.Model):
    __tablename__ = "user_progress"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey("challenges.id"), nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="progress")
    challenge = db.relationship("Challenge")
