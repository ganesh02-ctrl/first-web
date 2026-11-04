from app.extensions import db
from app.models.base import TimestampMixin
from app.utils.constants import STANDARD_DOCUMENT_TYPES
from app.utils.timeutils import days_until, isoformat


class DocumentFolder(TimestampMixin, db.Model):
    __tablename__ = "document_folders"
    __table_args__ = (db.UniqueConstraint("user_id", "name", name="uq_folder_user_name"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)

    user = db.relationship("User", back_populates="folders")
    documents = db.relationship("UploadedDocument", back_populates="folder")

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "document_count": len(self.documents)}


class UploadedDocument(TimestampMixin, db.Model):
    """Private file metadata. The file lives at UPLOAD_FOLDER/<user_id>/<stored_filename>."""
    __tablename__ = "uploaded_documents"
    __table_args__ = (db.Index("ix_documents_user_type", "user_id", "document_type"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    folder_id = db.Column(db.Integer, db.ForeignKey("document_folders.id", ondelete="SET NULL"),
                          nullable=True, index=True)
    display_name = db.Column(db.String(200), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(100), nullable=False, unique=True)
    mime_type = db.Column(db.String(100), nullable=False)
    size_bytes = db.Column(db.Integer, nullable=False)
    sha256 = db.Column(db.String(64), nullable=False)
    document_type = db.Column(db.String(50), nullable=False, default="other")
    issued_on = db.Column(db.Date, nullable=True)
    expires_on = db.Column(db.Date, nullable=True, index=True)

    user = db.relationship("User", back_populates="documents")
    folder = db.relationship("DocumentFolder", back_populates="documents")

    @property
    def previewable(self) -> bool:
        return self.mime_type in {"application/pdf", "image/png", "image/jpeg", "image/webp"}

    def to_dict(self) -> dict:
        left = days_until(self.expires_on)
        return {
            "id": self.id,
            "display_name": self.display_name,
            "original_filename": self.original_filename,
            "mime_type": self.mime_type,
            "size_bytes": self.size_bytes,
            "document_type": self.document_type,
            "document_type_label": STANDARD_DOCUMENT_TYPES.get(self.document_type, self.document_type),
            "folder_id": self.folder_id,
            "folder_name": self.folder.name if self.folder else None,
            "issued_on": isoformat(self.issued_on),
            "expires_on": isoformat(self.expires_on),
            "days_to_expiry": left,
            "is_expired": left is not None and left < 0,
            "previewable": self.previewable,
            "created_at": isoformat(self.created_at),
        }
