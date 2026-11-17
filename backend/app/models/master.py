"""Institution-wide, versioned policy; records stay in the original tables."""
from app.extensions import db
from app.models.base import TimestampMixin


class AcademicPolicy(TimestampMixin, db.Model):
    __tablename__ = "academic_policy"

    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.Integer, nullable=False, default=1)
    configuration = db.Column(db.JSON, nullable=False)
