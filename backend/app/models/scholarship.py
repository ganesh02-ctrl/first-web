from app.extensions import db
from app.models.base import TimestampMixin
from app.utils.constants import (ELIGIBILITY_CRITERIA, PROVIDER_TYPES, SCHOLARSHIP_TYPES,
                                 STANDARD_DOCUMENT_TYPES, VERIFICATION_STATUSES)
from app.utils.timeutils import days_until, isoformat, today_local


class ScholarshipCategory(TimestampMixin, db.Model):
    __tablename__ = "scholarship_categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    slug = db.Column(db.String(120), nullable=False, unique=True)
    description = db.Column(db.String(500), nullable=True)

    scholarships = db.relationship("Scholarship", back_populates="category")

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "slug": self.slug, "description": self.description}


class Scholarship(TimestampMixin, db.Model):
    """A scholarship record. Must carry provenance (source + verification) to be published."""
    __tablename__ = "scholarships"
    __table_args__ = (
        db.Index("ix_scholarships_publish_deadline", "is_published", "application_close_date"),
    )

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, index=True)
    slug = db.Column(db.String(280), nullable=False, unique=True)
    provider_name = db.Column(db.String(255), nullable=False)
    provider_type = db.Column(db.Enum(*PROVIDER_TYPES, name="provider_type"), nullable=False)
    scholarship_type = db.Column(db.Enum(*SCHOLARSHIP_TYPES, name="scholarship_type"),
                                 nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey("scholarship_categories.id", ondelete="SET NULL"),
                            nullable=True, index=True)
    state = db.Column(db.String(80), nullable=True, index=True)  # NULL => all-India
    academic_year = db.Column(db.String(20), nullable=True)
    description = db.Column(db.Text, nullable=True)
    benefits = db.Column(db.Text, nullable=True)
    amount_text = db.Column(db.String(255), nullable=True)
    amount_max = db.Column(db.Numeric(12, 2), nullable=True)
    application_open_date = db.Column(db.Date, nullable=True)
    application_close_date = db.Column(db.Date, nullable=True, index=True)

    # Provenance
    official_source_name = db.Column(db.String(255), nullable=False)
    source_url = db.Column(db.String(1000), nullable=False)
    application_url = db.Column(db.String(1000), nullable=False)
    verification_status = db.Column(db.Enum(*VERIFICATION_STATUSES, name="verification_status"),
                                    nullable=False, default="unverified", index=True)
    last_verified_at = db.Column(db.DateTime, nullable=True)
    verified_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    verification_notes = db.Column(db.Text, nullable=True)
    is_published = db.Column(db.Boolean, nullable=False, default=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    category = db.relationship("ScholarshipCategory", back_populates="scholarships")
    eligibility = db.relationship("ScholarshipEligibility", back_populates="scholarship",
                                  cascade="all, delete-orphan", order_by="ScholarshipEligibility.id")
    required_documents = db.relationship("ScholarshipDocument", back_populates="scholarship",
                                         cascade="all, delete-orphan", order_by="ScholarshipDocument.id")
    verified_by = db.relationship("User", foreign_keys=[verified_by_id])
    created_by = db.relationship("User", foreign_keys=[created_by_id])

    @property
    def is_expired(self) -> bool:
        return self.application_close_date is not None and self.application_close_date < today_local()

    @property
    def effective_status(self) -> str:
        """Display status: deadline passing always overrides 'verified'."""
        if self.is_expired or self.verification_status == "expired":
            return "expired"
        return self.verification_status

    def education_levels(self) -> list[str]:
        return [e.value for e in self.eligibility if e.criterion_type == "education_level" and e.value]

    def to_summary(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "slug": self.slug,
            "provider_name": self.provider_name,
            "provider_type": self.provider_type,
            "scholarship_type": self.scholarship_type,
            "category": self.category.to_dict() if self.category else None,
            "state": self.state,
            "academic_year": self.academic_year,
            "amount_text": self.amount_text,
            "amount_max": float(self.amount_max) if self.amount_max is not None else None,
            "application_open_date": isoformat(self.application_open_date),
            "application_close_date": isoformat(self.application_close_date),
            "days_left": days_until(self.application_close_date),
            "education_levels": self.education_levels(),
            "verification_status": self.verification_status,
            "effective_status": self.effective_status,
            "last_verified_at": isoformat(self.last_verified_at),
            "official_source_name": self.official_source_name,
            "is_published": self.is_published,
        }

    def to_detail(self) -> dict:
        data = self.to_summary()
        data.update({
            "description": self.description,
            "benefits": self.benefits,
            "source_url": self.source_url,
            "application_url": self.application_url,
            "verification_notes": self.verification_notes,
            "eligibility": [e.to_dict() for e in self.eligibility],
            "required_documents": [d.to_dict() for d in self.required_documents],
            "updated_at": isoformat(self.updated_at),
        })
        return data


class ScholarshipEligibility(db.Model):
    """One eligibility criterion per row (structured value + human-readable description)."""
    __tablename__ = "scholarship_eligibility"
    __table_args__ = (db.Index("ix_eligibility_type_value", "criterion_type", "value"),)

    id = db.Column(db.Integer, primary_key=True)
    scholarship_id = db.Column(db.Integer, db.ForeignKey("scholarships.id", ondelete="CASCADE"),
                               nullable=False, index=True)
    criterion_type = db.Column(db.Enum(*ELIGIBILITY_CRITERIA, name="eligibility_criterion"), nullable=False)
    value = db.Column(db.String(120), nullable=True)           # e.g. "undergraduate", "SC", "Karnataka"
    numeric_value = db.Column(db.Numeric(12, 2), nullable=True)  # e.g. max income, min percentage
    description = db.Column(db.String(1000), nullable=False)

    scholarship = db.relationship("Scholarship", back_populates="eligibility")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "criterion_type": self.criterion_type,
            "value": self.value,
            "numeric_value": float(self.numeric_value) if self.numeric_value is not None else None,
            "description": self.description,
        }


class ScholarshipDocument(db.Model):
    """A document required by a scholarship (checklist item)."""
    __tablename__ = "scholarship_documents"

    id = db.Column(db.Integer, primary_key=True)
    scholarship_id = db.Column(db.Integer, db.ForeignKey("scholarships.id", ondelete="CASCADE"),
                               nullable=False, index=True)
    document_type = db.Column(db.String(50), nullable=False, default="other")
    name = db.Column(db.String(255), nullable=False)
    is_mandatory = db.Column(db.Boolean, nullable=False, default=True)
    notes = db.Column(db.String(500), nullable=True)

    scholarship = db.relationship("Scholarship", back_populates="required_documents")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "document_type": self.document_type,
            "document_type_label": STANDARD_DOCUMENT_TYPES.get(self.document_type, self.document_type),
            "name": self.name,
            "is_mandatory": self.is_mandatory,
            "notes": self.notes,
        }
