"""
Configuration File for Player Verification System
"""
import os

class Config:
    """Base configuration"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database settings
    DATABASE_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'verification_system.db')
    
    # Session settings
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    PERMANENT_SESSION_LIFETIME = 28800  # 8 hours in seconds
    
    # Face recognition settings
    FACE_RECOGNITION_TOLERANCE = 0.6  # Lower is more strict (0.0-1.0)
    FACE_CAPTURE_COUNT = 5  # Number of images to capture during registration
    
    # Verification settings
    VERIFICATION_INTERVAL = 30  # Seconds between verification checks
    
    # File storage settings
    LOGS_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs', 'images')
    
    # Server settings
    HOST = '0.0.0.0'
    PORT = 5000
    DEBUG = True  # Set to False in production
    
    # WebSocket settings
    SOCKETIO_ASYNC_MODE = 'eventlet'
    
    # Admin roles
    ADMIN_ROLES = ['super_admin', 'tournament_admin']

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    
class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True  # Require HTTPS
    
    # Override with environment variables
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-must-set-secret-key-in-production'

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    DATABASE_PATH = ':memory:'  # Use in-memory database for tests

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(env='default'):
    """Get configuration by environment name"""
    return config.get(env, config['default'])
