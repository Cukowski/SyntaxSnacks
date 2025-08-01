from flask import Flask
from config import Config
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import db, User
import os

login_manager = LoginManager()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__, static_folder="../static", template_folder="templates")
    app.config.from_object(Config)

    # ensure instance folder exists
    os.makedirs(os.path.join(app.instance_path), exist_ok=True)

    # initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"

    from .auth.routes import auth_bp
    from .main.routes import main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    with app.app_context():
        db.create_all()

    return app
