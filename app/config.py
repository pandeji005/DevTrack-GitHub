import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///devtrack.db')
    if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    GITHUB_CLIENT_ID = os.environ.get('GITHUB_CLIENT_ID')
    GITHUB_CLIENT_SECRET = os.environ.get('GITHUB_CLIENT_SECRET')
    GITHUB_CALLBACK_URL = os.environ.get('GITHUB_CALLBACK_URL', 'http://localhost:5000/auth/github/callback')
    
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
    SOCKET_ASYNC_MODE = os.environ.get('SOCKET_ASYNC_MODE', 'eventlet')
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')
    
    # Session settings
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_NAME = 'devtrack_session'
