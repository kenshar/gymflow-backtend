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
    
    # Configure CORS - Allow GitHub Pages and all necessary headers
    CORS(app,
         resources={r"/api/*": {
             "origins": ["https://kenshar.github.io", "http://localhost:5173", "http://localhost:3000"],
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization"],
             "expose_headers": ["Content-Type", "Authorization"],
             "supports_credentials": True,
             "max_age": 3600
         }})
    
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
    
    # Health check endpoints
    @app.route('/', methods=['GET'])
    def health():
        from flask import jsonify
        return jsonify({'status': 'Backend is running', 'message': 'GymFlow API is online'}), 200
    
    @app.route('/api', methods=['GET'])
    def api_info():
        from flask import jsonify
        return jsonify({'message': 'GymFlow API', 'version': '1.0'}), 200
    
    return app
