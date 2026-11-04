from app.extensions import db
from app.models.base import TimestampMixin
from app.utils.constants import REPORT_REASONS, REPORT_STATUSES
from app.utils.timeutils import isoformat, utcnow


class AdminLog(db.Model):
    __tablename__ = "admin_logs"
    __table_args__ = (db.Index("ix_admin_logs_entity", "entity_type", "entity_id"),)

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = db.Column(db.String(80), nullable=False, index=True)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.JSON, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)

    admin = db.relationship("User")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "admin_email": self.admin.email if self.admin else None,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "created_at": isoformat(self.created_at),
        }


class ScholarshipReport(TimestampMixin, db.Model):
    """User-submitted report of incorrect scholarship information."""
    __tablename__ = "scholarship_reports"

    id = db.Column(db.Integer, primary_key=True)
    scholarship_id = db.Column(db.Integer, db.ForeignKey("scholarships.id", ondelete="CASCADE"),
                               nullable=False, index=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reason = db.Column(db.Enum(*REPORT_REASONS, name="report_reason"), nullable=False)
    details = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum(*REPORT_STATUSES, name="report_status"), nullable=False,
                       default="open", index=True)
    admin_notes = db.Column(db.Text, nullable=True)
    resolved_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)

    scholarship = db.relationship("Scholarship")
    reporter = db.relationship("User", foreign_keys=[reporter_id])
    resolved_by = db.relationship("User", foreign_keys=[resolved_by_id])

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "scholarship_id": self.scholarship_id,
            "scholarship_title": self.scholarship.title if self.scholarship else None,
            "reporter_email": self.reporter.email if self.reporter else None,
            "reason": self.reason,
            "details": self.details,
            "status": self.status,
            "admin_notes": self.admin_notes,
            "resolved_by": self.resolved_by.email if self.resolved_by else None,
            "resolved_at": isoformat(self.resolved_at),
            "created_at": isoformat(self.created_at),
        }
