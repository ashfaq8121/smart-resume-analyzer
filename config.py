
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    # ── Security ──────────────────────────────────────────────────
    # Flask uses this to sign session cookies and CSRF tokens.
    # In production, set this as an environment variable.
    SECRET_KEY = os.environ.get('SECRET_KEY', 'smart-resume-analyzer-secret-key-2024')

    # ── File Upload ───────────────────────────────────────────────
    UPLOAD_FOLDER      = os.path.join(BASE_DIR, 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'docx'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024   # 16 MB limit

    # ── Skills Database ───────────────────────────────────────────
    SKILLS_DB_PATH = os.path.join(BASE_DIR, 'data', 'skills_db.json')

    # ── SQLite Database (NEW) ─────────────────────────────────────
    # Stored as a file in your project root.
    # Switch to postgresql://user:pass@host/dbname for production.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f'sqlite:///{os.path.join(BASE_DIR, "resume_analyzer.db")}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False   # suppresses SQLAlchemy warning

    # ── Flask-Session (filesystem) ────────────────────────────────
    # Fixes the "cookie too large" bug when ranking 10 resumes.
    SESSION_TYPE           = 'filesystem'
    SESSION_FILE_DIR       = os.path.join(BASE_DIR, 'flask_sessions')
    SESSION_PERMANENT      = False
    SESSION_USE_SIGNER     = True
    SESSION_FILE_THRESHOLD = 500

    # ── Debug ─────────────────────────────────────────────────────
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'


# class ProductionConfig(Config):
#     DEBUG      = False
#     SECRET_KEY = os.environ.get('SECRET_KEY')   # must be set in environment

# class ProductionConfig(Config):
#     DEBUG = False
#     SECRET_KEY = os.environ.get('SECRET_KEY') or 'CHANGE-ME-IN-PRODUCTION'
# class DevelopmentConfig(Config):
#     DEBUG = True
class ProductionConfig(Config):
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fallback-change-me'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{os.path.join(BASE_DIR, "resume_analyzer.db")}'

config = {
    'development': DevelopmentConfig,
    'production':  ProductionConfig,
    'default':     DevelopmentConfig,
}
