"""SSS backend application factory."""
import logging
import os
from pathlib import Path

from flask import Flask
from sqlalchemy import text

from app.config import get_config
from app.extensions import cors, db, jwt, limiter, migrate
from app.utils.responses import success, error

BACKEND_DIR = Path(__file__).resolve().parent.parent


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__)
    config_class = get_config(config_name)
    config_class.validate()
    app.config.from_object(config_class)

    _configure_logging(app)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db, directory=str(BACKEND_DIR / "migrations"))
    jwt.init_app(app)
    limiter.init_app(app)
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        expose_headers=["Content-Disposition"],
        supports_credentials=False,
    )

    # Import models so SQLAlchemy / Alembic see every table.
    from app import models  # noqa: F401
    from app.middleware.jwt_handlers import register_jwt_handlers
    from app.utils.errors import register_error_handlers
    from app.routes import register_blueprints
    from app.cli import register_commands

    register_jwt_handlers(jwt)
    register_error_handlers(app)
    register_blueprints(app)
    register_commands(app)
    _register_security_headers(app)
    _register_health(app)
    _maybe_start_scheduler(app)
    _seed_initial_users(app)
    return app


def _configure_logging(app: Flask) -> None:
    level = logging.DEBUG if app.debug else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")


def _register_security_headers(app: Flask) -> None:
    @app.after_request
    def set_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Cache-Control", "no-store")
        return response


def _register_health(app: Flask) -> None:
    @app.get("/health")
    @app.get("/api/health")
    @limiter.exempt
    def health():
        try:
            db.session.execute(text("SELECT 1"))
            db_ok = True
        except Exception:  # pragma: no cover - depends on environment
            app.logger.exception("Database health check failed")
            db_ok = False
        payload = {
            "database": "up" if db_ok else "down",
            "email_configured": bool(app.config["SMTP_HOST"]),
            "sms_provider": app.config["SMS_PROVIDER"],
            "scheduler_enabled": app.config["SCHEDULER_ENABLED"],
        }
        if not db_ok:
            return error("Database unavailable", status=503, code="db_unavailable", details=payload)
        return success(payload)


def _maybe_start_scheduler(app: Flask) -> None:
    if app.config.get("TESTING") or not app.config.get("SCHEDULER_ENABLED"):
        return
    # With the Werkzeug reloader, only start in the child process to avoid duplicate jobs.
    if app.debug and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        return


def _seed_initial_users(app: Flask) -> None:
    if app.config.get("TESTING"):
        return
    with app.app_context():
        try:
            from app.models import User, StudentProfile, NotificationPreference
            from app.utils.timeutils import utcnow

            def ensure_user(email: str, password: str, name: str, role: str):
                u = User.query.filter_by(email=email).first()
                if not u:
                    u = User(email=email, role=role, is_active=True)
                    u.profile = StudentProfile(full_name=name)
                    u.notification_preference = NotificationPreference(email_enabled=False)
                    db.session.add(u)
                u.is_active = True
                u.role = role
                u.set_password(password)
                u.email_verified_at = u.email_verified_at or utcnow()
                u.failed_login_count = 0
                u.locked_until = None

            ensure_user("admin@sss.edu", "Admin@123456", "System Administrator", "admin")
            ensure_user("ganeshhidaduggi5@gmail.com", "Student@12345", "Ganesh", "student")
            ensure_user("ganeshhidaduggi5@gmil.com", "Student@12345", "Ganesh", "student")
            db.session.commit()
        except Exception as e:
            app.logger.warning(f"Could not seed initial users: {e}")
            db.session.rollback()
    from app.services.scheduler import start_scheduler
    start_scheduler(app)
