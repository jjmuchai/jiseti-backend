from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from dotenv import load_dotenv
from pathlib import Path
import os
import logging
from datetime import datetime

from models import db
from routes import register_routes

# Load environment variables
load_dotenv(dotenv_path=Path('.') / '.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # CORS Configuration - COMPREHENSIVE FIX
    # Handle multiple scenarios: with and without /api prefix, different origins
    CORS(app, 
         resources={
             r"/api/*": {
                 "origins": [
                     "http://localhost:5173",    # Vite dev server
                     "http://127.0.0.1:5173",   # Alternative localhost
                     "http://localhost:3000",   # Alternative React dev server
                     "http://localhost:5174",   # Alternative Vite port
                     "https://jiseti.go.ke", 
                     "https://jiseti.netlify.app"     # Production domain (if applicable)
                 ],
                 "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
                 "allow_headers": [
                     "Content-Type", 
                     "Authorization", 
                     "Access-Control-Allow-Credentials",
                     "Access-Control-Allow-Origin",
                     "X-Requested-With",
                     "Accept",
                     "Origin"
                 ],
                 "supports_credentials": True,
                 "expose_headers": ["Content-Range", "X-Content-Range"],
                 "max_age": 600  # Cache preflight for 10 minutes
             },
             r"/*": {  # Fallback for routes without /api prefix (your current setup)
                 "origins": [
                     "http://localhost:5173",
                     "http://127.0.0.1:5173", 
                     "http://localhost:3000",
                     "http://localhost:5174",
                     "https://jiseti.go.ke",
                     "https://jiseti.netlify.app"
                 ],
                 "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
                 "allow_headers": [
                     "Content-Type", 
                     "Authorization", 
                     "Access-Control-Allow-Credentials",
                     "Access-Control-Allow-Origin",
                     "X-Requested-With",
                     "Accept",
                     "Origin"
                 ],
                 "supports_credentials": True,
                 "expose_headers": ["Content-Range", "X-Content-Range"],
                 "max_age": 600
             }
         })
    
    # Database Configuration
    database_url = os.getenv('SQLALCHEMY_DATABASE_URI')
    if not database_url:
        # Fallback to SQLite for development
        database_url = 'sqlite:///jiseti.db'
        logger.warning("No DATABASE_URL found, using SQLite fallback")
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,  # Verify connections before use
        'pool_recycle': 300,    # Recycle connections every 5 minutes
    }
    
    # JWT Configuration
    jwt_secret = os.getenv('JWT_SECRET_KEY')
    if not jwt_secret:
        jwt_secret = 'dev-secret-key-change-in-production'
        logger.warning("No JWT_SECRET_KEY found, using development key")
    
    app.config['JWT_SECRET_KEY'] = jwt_secret
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False  # Tokens don't expire for simplicity
    
    # CORS Fix: Handle preflight requests explicitly
    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = jsonify({'status': 'OK'})
            
            # Get the origin from the request
            origin = request.headers.get('Origin')
            
            # List of allowed origins
            allowed_origins = [
                'http://localhost:5173',
                'http://127.0.0.1:5173',
                'http://localhost:3000', 
                'http://localhost:5174',
                'https://jiseti.go.ke',
                "https://jiseti.netlify.app"
            ]
            
            # Set CORS headers if origin is allowed
            if origin in allowed_origins:
                response.headers['Access-Control-Allow-Origin'] = origin
                response.headers['Access-Control-Allow-Credentials'] = 'true'
                response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, PATCH, OPTIONS'
                response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept, Origin'
                response.headers['Access-Control-Max-Age'] = '600'
            
            return response
    
    # CORS Fix: Add headers to all responses as backup
    @app.after_request
    def after_request(response):
        # Get the origin from the request
        origin = request.headers.get('Origin')
        
        # List of allowed origins
        allowed_origins = [
            'http://localhost:5173',
            'http://127.0.0.1:5173',
            'http://localhost:3000',
            'http://localhost:5174', 
            'https://jiseti.go.ke',
            "https://jiseti.netlify.app"
        ]
        
        # Add CORS headers if origin is allowed
        if origin in allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, PATCH, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept, Origin'
        
        # Security headers (unchanged from original)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        return response
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    jwt = JWTManager(app)
    
    # Register routes (unchanged from original)
    register_routes(app)
    
    # Health check endpoint (unchanged from original)
    @app.route('/')
    def home():
        return jsonify({
            "message": "Welcome to Jiseti API",
            "version": "2.0",
            "status": "running",
            "endpoints": {
                "authentication": "/auth/*",
                "records": "/records/*", 
                "admin": "/admin/*",
                "public": "/public/*"
            }
        }), 200
    
    @app.route('/health')
    def health_check():
        """Health check endpoint for monitoring"""
        try:
            # Test database connection
            db.session.execute('SELECT 1')
            return jsonify({
                "status": "healthy",
                "database": "connected",
                "timestamp": str(datetime.utcnow())
            }), 200
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return jsonify({
                "status": "unhealthy", 
                "database": "disconnected",
                "error": str(e)
            }), 500
    
    # Error handlers (unchanged from original)
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Endpoint not found',
            'message': 'The requested resource does not exist'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        logger.error(f"Internal server error: {str(error)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Something went wrong on our end'
        }), 500
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Bad request',
            'message': 'Invalid request data'
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Authentication required'
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'error': 'Forbidden',
            'message': 'Insufficient permissions'
        }), 403
    
    # JWT error handlers (unchanged from original)
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'error': 'Token expired',
            'message': 'Your session has expired. Please log in again.'
        }), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            'error': 'Invalid token',
            'message': 'Invalid authentication token'
        }), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            'error': 'Token required',
            'message': 'Authentication token is required'
        }), 401
    
    return app

# Create the app instance
app = create_app()

if __name__ == '__main__':
    with app.app_context():
        try:
            # Create all database tables
            db.create_all()
            logger.info("Database tables created successfully")
            
            # Check if we need to create a default admin
            from models import Administrator
            from werkzeug.security import generate_password_hash
            
            if not Administrator.query.first():
                default_admin = Administrator(
                    name="Default Admin",
                    email="admin@jiseti.go.ke",
                    password=generate_password_hash("admin123"),
                    admin_number="ADM-DEFAULT-001"
                )
                db.session.add(default_admin)
                db.session.commit()
                logger.info("Default admin created: admin@jiseti.go.ke / admin123")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
    
    # Run the development server
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    logger.info(f"Starting Jiseti API server on port {port}")
    # CORS Fix: Bind to all interfaces so frontend can reach backend
    app.run(debug=debug, port=port, host='0.0.0.0')
