from app.extensions import db
from app.models.base import TimestampMixin
from app.utils.timeutils import isoformat


class StudentProfile(TimestampMixin, db.Model):
    __tablename__ = "student_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"),
                        nullable=False, unique=True)
    full_name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(30), nullable=True)
    state = db.Column(db.String(80), nullable=True, index=True)
    district = db.Column(db.String(80), nullable=True)
    college = db.Column(db.String(200), nullable=True)
    university = db.Column(db.String(200), nullable=True)
    degree = db.Column(db.String(120), nullable=True)
    branch = db.Column(db.String(120), nullable=True)
    education_level = db.Column(db.String(30), nullable=True)
    current_semester = db.Column(db.SmallInteger, nullable=True)
    graduation_year = db.Column(db.SmallInteger, nullable=True)
    social_category = db.Column(db.String(30), nullable=True)
    annual_family_income = db.Column(db.Numeric(12, 2), nullable=True)
    academic_summary = db.Column(db.Text, nullable=True)
    preferred_scholarship_types = db.Column(db.JSON, nullable=True)
    preferred_states = db.Column(db.JSON, nullable=True)
    public_portfolio_enabled = db.Column(db.Boolean, nullable=False, default=False)
    public_slug = db.Column(db.String(32), nullable=True, unique=True)

    user = db.relationship("User", back_populates="profile")

    def to_dict(self) -> dict:
        return {
            "full_name": self.full_name,
            "email": self.user.email if self.user else None,
            "phone": self.phone,
            "date_of_birth": isoformat(self.date_of_birth),
            "gender": self.gender,
            "state": self.state,
            "district": self.district,
            "college": self.college,
            "university": self.university,
            "degree": self.degree,
            "branch": self.branch,
            "education_level": self.education_level,
            "current_semester": self.current_semester,
            "graduation_year": self.graduation_year,
            "social_category": self.social_category,
            "annual_family_income": float(self.annual_family_income)
            if self.annual_family_income is not None else None,
            "academic_summary": self.academic_summary,
            "preferred_scholarship_types": self.preferred_scholarship_types or [],
            "preferred_states": self.preferred_states or [],
            "public_portfolio_enabled": self.public_portfolio_enabled,
            "public_slug": self.public_slug if self.public_portfolio_enabled else None,
            "updated_at": isoformat(self.updated_at),
        }
