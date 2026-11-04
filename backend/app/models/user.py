from app.extensions import db
from app.models.base import TimestampMixin
from app.utils.constants import ROLES
from app.utils.security import hash_password, verify_password
from app.utils.timeutils import isoformat, utcnow


class User(TimestampMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(*ROLES, name="user_role"), nullable=False, default="student", index=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    email_verified_at = db.Column(db.DateTime, nullable=True)
    last_login_at = db.Column(db.DateTime, nullable=True)
    failed_login_count = db.Column(db.Integer, nullable=False, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    # Any JWT issued before this moment is rejected (password change / reset signs out all sessions).
    password_changed_at = db.Column(db.DateTime, nullable=True)

    profile = db.relationship("StudentProfile", back_populates="user", uselist=False,
                              cascade="all, delete-orphan")
    notification_preference = db.relationship("NotificationPreference", back_populates="user",
                                              uselist=False, cascade="all, delete-orphan")
    tracked_scholarships = db.relationship("TrackedScholarship", back_populates="user",
                                           cascade="all, delete-orphan", lazy="dynamic")
    applications = db.relationship("ScholarshipApplication", back_populates="user",
                                   cascade="all, delete-orphan", lazy="dynamic")
    notifications = db.relationship("Notification", back_populates="user",
                                    cascade="all, delete-orphan", lazy="dynamic")
    semesters = db.relationship("Semester", back_populates="user", cascade="all, delete-orphan",
                                order_by="Semester.number")
    achievements = db.relationship("Achievement", back_populates="user",
                                   cascade="all, delete-orphan", lazy="dynamic")
    documents = db.relationship("UploadedDocument", back_populates="user",
                                cascade="all, delete-orphan", lazy="dynamic")
    folders = db.relationship("DocumentFolder", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, raw: str) -> None:
        self.password_hash = hash_password(raw)
        # JWT 'iat' has one-second resolution, so store whole seconds.
        self.password_changed_at = utcnow().replace(microsecond=0)

    def check_password(self, raw: str) -> bool:
        return verify_password(raw, self.password_hash)

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def email_verified(self) -> bool:
        return self.email_verified_at is not None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "email_verified": self.email_verified,
            "last_login_at": isoformat(self.last_login_at),
            "created_at": isoformat(self.created_at),
            "full_name": self.profile.full_name if self.profile else None,
        }
