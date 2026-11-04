"""Blueprint registration."""
from flask import Flask


def register_blueprints(app: Flask) -> None:
    from app.routes.academics import bp as academics_bp
    from app.routes.achievements import bp as achievements_bp
    from app.routes.admin import bp as admin_bp
    from app.routes.auth import bp as auth_bp
    from app.routes.documents import bp as documents_bp
    from app.routes.notifications import bp as notifications_bp
    from app.routes.public import bp as public_bp
    from app.routes.scholarships import bp as scholarships_bp
    from app.routes.students import bp as students_bp
    from app.routes.tracking import bp as tracking_bp

    for bp in (auth_bp, students_bp, scholarships_bp, tracking_bp, academics_bp, achievements_bp,
               documents_bp, notifications_bp, admin_bp, public_bp):
        app.register_blueprint(bp)
