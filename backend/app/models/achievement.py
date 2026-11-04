from app.extensions import db
from app.models.base import TimestampMixin
from app.utils.constants import ACHIEVEMENT_CATEGORIES
from app.utils.timeutils import isoformat


class Achievement(TimestampMixin, db.Model):
    __tablename__ = "achievements"
    __table_args__ = (db.Index("ix_achievements_user_date", "user_id", "achieved_on"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    organization = db.Column(db.String(200), nullable=True)
    category = db.Column(db.Enum(*ACHIEVEMENT_CATEGORIES, name="achievement_category"),
                         nullable=False, index=True)
    achieved_on = db.Column(db.Date, nullable=False)
    rank_position = db.Column(db.String(100), nullable=True)
    location_name = db.Column(db.String(255), nullable=True)
    latitude = db.Column(db.Numeric(9, 6), nullable=True)
    longitude = db.Column(db.Numeric(9, 6), nullable=True)
    certificate_document_id = db.Column(db.Integer, db.ForeignKey("uploaded_documents.id", ondelete="SET NULL"),
                                        nullable=True)
    is_public = db.Column(db.Boolean, nullable=False, default=False)

    user = db.relationship("User", back_populates="achievements")
    certificate = db.relationship("UploadedDocument")

    def to_dict(self, public: bool = False) -> dict:
        data = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "organization": self.organization,
            "category": self.category,
            "achieved_on": isoformat(self.achieved_on),
            "rank_position": self.rank_position,
            "location_name": self.location_name,
            "latitude": float(self.latitude) if self.latitude is not None else None,
            "longitude": float(self.longitude) if self.longitude is not None else None,
        }
        if not public:
            # Private fields: certificate access always goes through authenticated endpoints.
            data.update({
                "is_public": self.is_public,
                "certificate_document_id": self.certificate_document_id,
                "certificate_name": self.certificate.display_name if self.certificate else None,
                "certificate_mime": self.certificate.mime_type if self.certificate else None,
                "created_at": isoformat(self.created_at),
            })
        return data
