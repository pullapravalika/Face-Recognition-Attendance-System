# app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from .config import Config
import os

# Initialize extensions here (globals)
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'main.login'
login_manager.login_message_category = 'info'
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Set upload folder path and create folder if missing
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/uploads')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    print(">>> Flask DB URI:", app.config['SQLALCHEMY_DATABASE_URI'])

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    from .admin_routes import admin_bp
    from .student_routes import student_bp
    from .main_routes import main_bp
    from app.api_routes import api_bp

    app.register_blueprint(admin_bp,url_prefix='/admin')
    app.register_blueprint(student_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)

    return app

