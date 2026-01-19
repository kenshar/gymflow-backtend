from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from app.models import db
import os
from dotenv import load_dotenv

load_dotenv()

migrate = Migrate()

def create_app(config_name="development"):
    app = Flask(__name__)
    
    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL',
        'postgresql://user:password@localhost/gymflow'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JSON_SORT_KEYS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    # Register blueprints
    from app.routes import auth_bp, members_bp, memberships_bp, attendance_bp, workouts_bp, admin_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(members_bp)
    app.register_blueprint(memberships_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(workouts_bp)
    app.register_blueprint(admin_bp)
    
    return app
