import os
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')


def normalize_db_url(url: str) -> str:
    if not url:
        return ""
    url = url.strip()
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


class Config:
    """Base Configuration."""
    BASE_DIR = BASE_DIR
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-portfolio-dax-prajapati-super-secret-key-2026")
    
    # Neon PostgreSQL Database Configuration
    raw_db_url = os.getenv("DATABASE_URL", "").strip()
    normalized_url = normalize_db_url(raw_db_url)
    
    if normalized_url and "YOUR_PASSWORD" not in normalized_url and "sample" not in normalized_url:
        SQLALCHEMY_DATABASE_URI = normalized_url
    else:
        # Local development fallback (handles serverless/Vercel read-only filesystem safely)
        if os.getenv("VERCEL"):
            instance_dir = Path("/tmp")
        else:
            instance_dir = BASE_DIR / "instance"
            try:
                instance_dir.mkdir(parents=True, exist_ok=True)
            except OSError:
                instance_dir = Path("/tmp")
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{instance_dir / 'portfolio.db'}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Neon Serverless connection pool optimization
    if "postgresql" in SQLALCHEMY_DATABASE_URI:
        is_serverless = os.getenv("VERCEL") == "1" or os.getenv("SERVERLESS") == "1"
        SQLALCHEMY_ENGINE_OPTIONS = {
            "pool_pre_ping": True,
            "pool_recycle": 120 if is_serverless else 300,
            "pool_size": 5 if is_serverless else 10,
            "max_overflow": 10 if is_serverless else 20,
        }
    else:
        SQLALCHEMY_ENGINE_OPTIONS = {}

    # Session & Cookie Security
    SESSION_COOKIE_NAME = "prajapati_session"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "True" if os.getenv("VERCEL") else "False").lower() == "true"
    PERMANENT_SESSION_LIFETIME = timedelta(seconds=int(os.getenv("PERMANENT_SESSION_LIFETIME", 86400)))

    # Uploads
    UPLOAD_FOLDER = BASE_DIR / "static" / "images" / "designs"
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "svg"}

    # Initial Admin Config
    ADMIN_NAME = os.getenv("ADMIN_NAME", "Dax Prajapati")
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@prajapatidax.co.in")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "AdminPass@2026!")

    # Security
    WTF_CSRF_TIME_LIMIT = 3600
    RATE_LIMIT_LOGIN_MAX = 5
    RATE_LIMIT_LOGIN_WINDOW = 600  # 10 minutes
    RATE_LIMIT_QUOTATION_MAX = 10
    RATE_LIMIT_QUOTATION_WINDOW = 3600  # 1 hour

    # Neon Object Storage S3 Configuration
    NEON_STORAGE_BUCKET = os.getenv("NEON_STORAGE_BUCKET", "photos")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_ENDPOINT_URL_S3 = os.getenv("AWS_ENDPOINT_URL_S3", "")
    AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-1")


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True


class TestingConfig(Config):
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {}
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
