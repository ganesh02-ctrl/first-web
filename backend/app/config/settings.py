"""Application configuration. All secrets come from environment variables."""
import os
from datetime import timedelta
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent

# Load root .env first, then an optional backend/.env override.
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(BACKEND_DIR / ".env", override=True)

INSECURE_DEFAULTS = {"", "change-me", "change-me-to-a-long-random-string",
                     "change-me-to-a-different-long-random-string"}


def _bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


def _database_uri() -> str:
    url = os.getenv("DATABASE_URL")
    if url:
        if url.startswith("mysql://"):
            url = url.replace("mysql://", "mysql+pymysql://", 1)
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url
    user = quote_plus(os.getenv("MYSQL_USER", "sss_user"))
    password = quote_plus(os.getenv("MYSQL_PASSWORD", ""))
    host = os.getenv("MYSQL_HOST", "127.0.0.1")
    port = os.getenv("MYSQL_PORT", "3306")
    name = os.getenv("MYSQL_DATABASE", "sss_db")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}?charset=utf8mb4"


def _upload_folder() -> str:
    folder = Path(os.getenv("UPLOAD_FOLDER", "uploads"))
    if not folder.is_absolute():
        folder = BACKEND_DIR / folder
    return str(folder)


class BaseConfig:
    APP_NAME = os.getenv("APP_NAME", "SSS - Student Support System")
    SECRET_KEY = os.getenv("SECRET_KEY", "")
    DEBUG = False
    TESTING = False
    APP_TIMEZONE = os.getenv("APP_TIMEZONE", "Asia/Kolkata")
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")

    # Database
    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 280}

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=_int("JWT_ACCESS_TOKEN_MINUTES", 30))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=_int("JWT_REFRESH_TOKEN_DAYS", 14))
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_HEADER_TYPE = "Bearer"
    BCRYPT_ROUNDS = _int("BCRYPT_ROUNDS", 12)

    # CORS / rate limiting
    CORS_ORIGINS = _list("CORS_ORIGINS", "http://localhost:5173")
    RATELIMIT_ENABLED = _bool("RATELIMIT_ENABLED", True)
    RATELIMIT_DEFAULT = os.getenv("RATELIMIT_DEFAULT", "300 per hour")
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_HEADERS_ENABLED = True

    # Uploads
    UPLOAD_FOLDER = _upload_folder()
    MAX_UPLOAD_MB = _int("MAX_UPLOAD_MB", 10)
    MAX_CONTENT_LENGTH = (MAX_UPLOAD_MB + 1) * 1024 * 1024  # small allowance for multipart overhead
    ALLOWED_UPLOAD_EXTENSIONS = set(_list("ALLOWED_UPLOAD_EXTENSIONS", "pdf,png,jpg,jpeg,webp"))

    # Email
    SMTP_HOST = os.getenv("SMTP_HOST", "")
    SMTP_PORT = _int("SMTP_PORT", 587)
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_USE_TLS = _bool("SMTP_USE_TLS", True)
    SMTP_USE_SSL = _bool("SMTP_USE_SSL", False)
    MAIL_FROM = os.getenv("MAIL_FROM", "SSS Student Support <no-reply@example.com>")
    EMAIL_MAX_RETRIES = _int("EMAIL_MAX_RETRIES", 3)
    EMAIL_RETRY_BASE_MINUTES = _int("EMAIL_RETRY_BASE_MINUTES", 10)

    # SMS
    SMS_PROVIDER = os.getenv("SMS_PROVIDER", "none").strip().lower()
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "")
    SMS_HTTP_ENDPOINT = os.getenv("SMS_HTTP_ENDPOINT", "")
    SMS_HTTP_API_KEY = os.getenv("SMS_HTTP_API_KEY", "")
    SMS_DEFAULT_COUNTRY_CODE = os.getenv("SMS_DEFAULT_COUNTRY_CODE", "+91")

    # Scheduler / reminders
    SCHEDULER_ENABLED = _bool("SCHEDULER_ENABLED", True)
    REMINDER_RUN_HOUR = _int("REMINDER_RUN_HOUR", 8)
    REMINDER_DAYS = sorted({int(d) for d in _list("REMINDER_DAYS", "30,15,7,3,1") if d.isdigit()},
                           reverse=True)
    DELIVERY_RETRY_INTERVAL_MINUTES = _int("DELIVERY_RETRY_INTERVAL_MINUTES", 15)

    # Token lifetimes
    PASSWORD_RESET_TOKEN_MINUTES = 30
    EMAIL_VERIFICATION_TOKEN_HOURS = 48

    @classmethod
    def validate(cls) -> None:
        """Hook for environment-specific validation."""


class DevelopmentConfig(BaseConfig):
    DEBUG = True

    @classmethod
    def validate(cls) -> None:
        # Development still refuses empty secrets so JWTs are never signed with "".
        if not cls.SECRET_KEY or not cls.JWT_SECRET_KEY:
            raise RuntimeError("SECRET_KEY and JWT_SECRET_KEY must be set in .env")


class TestingConfig(BaseConfig):
    TESTING = True
    SECRET_KEY = "test-secret-key-not-for-production"
    JWT_SECRET_KEY = "test-jwt-secret-key-not-for-production-use"
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")
    SQLALCHEMY_ENGINE_OPTIONS = {}
    BCRYPT_ROUNDS = 4
    RATELIMIT_ENABLED = False
    SCHEDULER_ENABLED = False
    SMTP_HOST = ""
    SMS_PROVIDER = "none"
    UPLOAD_FOLDER = str(BACKEND_DIR / "tests" / "_uploads")


class ProductionConfig(BaseConfig):
    @classmethod
    def validate(cls) -> None:
        problems = []
        if cls.SECRET_KEY in INSECURE_DEFAULTS or len(cls.SECRET_KEY) < 32:
            problems.append("SECRET_KEY must be set to a random value of at least 32 characters")
        if cls.JWT_SECRET_KEY in INSECURE_DEFAULTS or len(cls.JWT_SECRET_KEY) < 32:
            problems.append("JWT_SECRET_KEY must be set to a random value of at least 32 characters")
        if not cls.CORS_ORIGINS:
            problems.append("CORS_ORIGINS must list the allowed frontend origins")
        if problems:
            raise RuntimeError("Invalid production configuration: " + "; ".join(problems))


_CONFIGS = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(name: str | None = None):
    key = (name or os.getenv("APP_ENV", "development")).strip().lower()
    if key not in _CONFIGS:
        raise RuntimeError(f"Unknown APP_ENV '{key}'. Use development, testing or production.")
    return _CONFIGS[key]
