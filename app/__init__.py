from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()

try:
    from flask_migrate import Migrate
    migrate = Migrate()
    MIGRATE_AVAILABLE = True
except ImportError:
    MIGRATE_AVAILABLE = False

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')

    # Get environment variables
    secret_key = os.environ.get('SECRET_KEY')
    database_url = os.environ.get('DATABASE_URL')

    # Validate required environment variables
    if not secret_key:
        raise ValueError("SECRET_KEY environment variable is required")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is required")

    app.config['SECRET_KEY'] = secret_key
    # Ensure PostgreSQL URL uses correct dialect
    if database_url.startswith('postgresql://'):
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url.replace('postgresql://', 'postgresql+pg8000://', 1)
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    if MIGRATE_AVAILABLE:
        migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from app.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    # Create database tables (but don't seed data in production)
    with app.app_context():
        db.create_all()

    return app