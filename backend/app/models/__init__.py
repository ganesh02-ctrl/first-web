"""Import every model so SQLAlchemy metadata and Alembic autogenerate see all tables."""
from app.models.user import User
from app.models.profile import StudentProfile
from app.models.scholarship import Scholarship, ScholarshipCategory, ScholarshipDocument, ScholarshipEligibility
from app.models.tracking import ApplicationStatusHistory, ScholarshipApplication, TrackedScholarship
from app.models.notification import Notification, NotificationDelivery, NotificationPreference
from app.models.academic import GradeMapping, GradingScale, Semester, Subject
from app.models.document import DocumentFolder, UploadedDocument
from app.models.achievement import Achievement
from app.models.admin import AdminLog, ScholarshipReport
from app.models.token import EmailVerificationToken, PasswordResetToken, TokenBlocklist

__all__ = [
    "User", "StudentProfile",
    "Scholarship", "ScholarshipCategory", "ScholarshipDocument", "ScholarshipEligibility",
    "TrackedScholarship", "ScholarshipApplication", "ApplicationStatusHistory",
    "Notification", "NotificationDelivery", "NotificationPreference",
    "GradingScale", "GradeMapping", "Semester", "Subject",
    "DocumentFolder", "UploadedDocument", "Achievement",
    "AdminLog", "ScholarshipReport",
    "PasswordResetToken", "EmailVerificationToken", "TokenBlocklist",
]
