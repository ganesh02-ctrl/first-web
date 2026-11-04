from app.extensions import db
from app.models.base import TimestampMixin
from app.utils.constants import APPLICATION_STATUSES, APPLICATION_STATUS_LABELS
from app.utils.timeutils import isoformat, utcnow


class TrackedScholarship(TimestampMixin, db.Model):
    """User ↔ scholarship link for bookmarks and deadline reminders."""
    __tablename__ = "tracked_scholarships"
    __table_args__ = (db.UniqueConstraint("user_id", "scholarship_id", name="uq_tracked_user_scholarship"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    scholarship_id = db.Column(db.Integer, db.ForeignKey("scholarships.id", ondelete="CASCADE"),
                               nullable=False, index=True)
    is_bookmarked = db.Column(db.Boolean, nullable=False, default=False)
    reminders_enabled = db.Column(db.Boolean, nullable=False, default=True)

    user = db.relationship("User", back_populates="tracked_scholarships")
    scholarship = db.relationship("Scholarship")

    def to_dict(self, application=None) -> dict:
        return {
            "id": self.id,
            "scholarship": self.scholarship.to_summary() if self.scholarship else None,
            "is_bookmarked": self.is_bookmarked,
            "reminders_enabled": self.reminders_enabled,
            "application": application.to_dict(include_history=False) if application else None,
            "created_at": isoformat(self.created_at),
        }


class ScholarshipApplication(TimestampMixin, db.Model):
    __tablename__ = "scholarship_applications"
    __table_args__ = (db.UniqueConstraint("user_id", "scholarship_id", name="uq_application_user_scholarship"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    scholarship_id = db.Column(db.Integer, db.ForeignKey("scholarships.id", ondelete="CASCADE"),
                               nullable=False, index=True)
    status = db.Column(db.Enum(*APPLICATION_STATUSES, name="application_status"),
                       nullable=False, default="interested", index=True)
    applied_on = db.Column(db.Date, nullable=True)
    application_reference = db.Column(db.String(120), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    user = db.relationship("User", back_populates="applications")
    scholarship = db.relationship("Scholarship")
    history = db.relationship("ApplicationStatusHistory", back_populates="application",
                              cascade="all, delete-orphan", order_by="ApplicationStatusHistory.changed_at")

    def change_status(self, new_status: str, note: str | None = None) -> None:
        if new_status == self.status and self.id is not None:
            return
        self.history.append(ApplicationStatusHistory(from_status=self.status if self.id else None,
                                                     to_status=new_status, note=note))
        self.status = new_status

    def to_dict(self, include_history: bool = True) -> dict:
        data = {
            "id": self.id,
            "scholarship_id": self.scholarship_id,
            "scholarship": self.scholarship.to_summary() if self.scholarship else None,
            "status": self.status,
            "status_label": APPLICATION_STATUS_LABELS[self.status],
            "applied_on": isoformat(self.applied_on),
            "application_reference": self.application_reference,
            "notes": self.notes,
            "updated_at": isoformat(self.updated_at),
        }
        if include_history:
            data["history"] = [h.to_dict() for h in self.history]
        return data


class ApplicationStatusHistory(db.Model):
    __tablename__ = "application_status_history"

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey("scholarship_applications.id", ondelete="CASCADE"),
                               nullable=False, index=True)
    from_status = db.Column(db.String(30), nullable=True)
    to_status = db.Column(db.String(30), nullable=False)
    note = db.Column(db.String(500), nullable=True)
    changed_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    application = db.relationship("ScholarshipApplication", back_populates="history")

    def to_dict(self) -> dict:
        return {
            "from_status": self.from_status,
            "to_status": self.to_status,
            "to_status_label": APPLICATION_STATUS_LABELS.get(self.to_status, self.to_status),
            "note": self.note,
            "changed_at": isoformat(self.changed_at),
        }
