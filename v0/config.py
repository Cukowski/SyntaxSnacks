import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

basedir = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "fallback-dev-key")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{basedir / 'instance' / 'syntaxsnacks.sqlite'}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"  # adjust to Strict if needed
    # In production, ensure you serve over HTTPS and set:
    # SESSION_COOKIE_SECURE = True
