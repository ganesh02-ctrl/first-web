from app.extensions import db
from app.models.base import TimestampMixin
from app.utils.gpa import calculate_sgpa
from app.utils.timeutils import isoformat


class GradingScale(TimestampMixin, db.Model):
    """A grade → grade-point mapping. owner_user_id NULL => shared template (admin-managed)."""
    __tablename__ = "grading_scales"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    max_grade_point = db.Column(db.Numeric(4, 2), nullable=False)
    owner_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"),
                              nullable=True, index=True)
    is_template = db.Column(db.Boolean, nullable=False, default=False)

    grades = db.relationship("GradeMapping", back_populates="scale", cascade="all, delete-orphan",
                             order_by="GradeMapping.sort_order")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "max_grade_point": float(self.max_grade_point),
            "is_template": self.is_template,
            "is_owned": self.owner_user_id is not None,
            "grades": [g.to_dict() for g in self.grades],
        }


class GradeMapping(db.Model):
    __tablename__ = "grade_mappings"
    __table_args__ = (db.UniqueConstraint("scale_id", "label", name="uq_grade_scale_label"),)

    id = db.Column(db.Integer, primary_key=True)
    scale_id = db.Column(db.Integer, db.ForeignKey("grading_scales.id", ondelete="CASCADE"), nullable=False)
    label = db.Column(db.String(10), nullable=False)
    grade_point = db.Column(db.Numeric(4, 2), nullable=False)
    min_percent = db.Column(db.Numeric(5, 2), nullable=True)
    max_percent = db.Column(db.Numeric(5, 2), nullable=True)
    counts_in_gpa = db.Column(db.Boolean, nullable=False, default=True)
    is_passing = db.Column(db.Boolean, nullable=False, default=True)
    sort_order = db.Column(db.SmallInteger, nullable=False, default=0)

    scale = db.relationship("GradingScale", back_populates="grades")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "grade_point": float(self.grade_point),
            "min_percent": float(self.min_percent) if self.min_percent is not None else None,
            "max_percent": float(self.max_percent) if self.max_percent is not None else None,
            "counts_in_gpa": self.counts_in_gpa,
            "is_passing": self.is_passing,
            "sort_order": self.sort_order,
        }


class Semester(TimestampMixin, db.Model):
    __tablename__ = "semesters"
    __table_args__ = (db.UniqueConstraint("user_id", "number", name="uq_semester_user_number"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    grading_scale_id = db.Column(db.Integer, db.ForeignKey("grading_scales.id", ondelete="SET NULL"),
                                 nullable=True)
    number = db.Column(db.SmallInteger, nullable=False)
    title = db.Column(db.String(100), nullable=True)
    academic_year = db.Column(db.String(20), nullable=True)
    notes = db.Column(db.String(500), nullable=True)

    user = db.relationship("User", back_populates="semesters")
    grading_scale = db.relationship("GradingScale")
    subjects = db.relationship("Subject", back_populates="semester", cascade="all, delete-orphan",
                               order_by="Subject.id")

    def to_dict(self, include_subjects: bool = True) -> dict:
        result = calculate_sgpa(self.subjects)
        data = {
            "id": self.id,
            "number": self.number,
            "title": self.title or f"Semester {self.number}",
            "academic_year": self.academic_year,
            "notes": self.notes,
            "grading_scale_id": self.grading_scale_id,
            "grading_scale_name": self.grading_scale.name if self.grading_scale else None,
            "sgpa": float(result.gpa) if result.gpa is not None else None,
            "total_credits": float(result.total_credits),
            "subject_count": len(self.subjects),
            "updated_at": isoformat(self.updated_at),
        }
        if include_subjects:
            data["subjects"] = [s.to_dict() for s in self.subjects]
        return data


class Subject(TimestampMixin, db.Model):
    """grade_point/counts_in_gpa are snapshots of the scale mapping at time of entry."""
    __tablename__ = "subjects"

    id = db.Column(db.Integer, primary_key=True)
    semester_id = db.Column(db.Integer, db.ForeignKey("semesters.id", ondelete="CASCADE"),
                            nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(30), nullable=True)
    credits = db.Column(db.Numeric(5, 2), nullable=False)
    grade_label = db.Column(db.String(10), nullable=False)
    grade_point = db.Column(db.Numeric(4, 2), nullable=False)
    counts_in_gpa = db.Column(db.Boolean, nullable=False, default=True)

    semester = db.relationship("Semester", back_populates="subjects")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "credits": float(self.credits),
            "grade_label": self.grade_label,
            "grade_point": float(self.grade_point),
            "counts_in_gpa": self.counts_in_gpa,
        }
