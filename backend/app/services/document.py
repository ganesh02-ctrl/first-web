"""Document vault: uploads, folders and missing-document checklist."""
from app.extensions import db
from app.models import Achievement, DocumentFolder, Scholarship, TrackedScholarship, UploadedDocument
from app.services import storage
from app.utils.constants import STANDARD_DOCUMENT_TYPES
from app.utils.errors import BadRequest, NotFound
from app.utils.timeutils import today_local


def get_owned(user, doc_id: int) -> UploadedDocument:
    doc = UploadedDocument.query.filter_by(id=doc_id, user_id=user.id).first()
    if not doc:
        raise NotFound("Document not found")  # same response for others' documents
    return doc


def _folder(user, folder_id):
    if folder_id is None:
        return None
    folder = DocumentFolder.query.filter_by(id=folder_id, user_id=user.id).first()
    if not folder:
        raise BadRequest("Folder not found")
    return folder


def list_documents(user, folder_id=None, document_type=None):
    query = UploadedDocument.query.filter_by(user_id=user.id)
    if folder_id is not None:
        query = query.filter_by(folder_id=folder_id)
    if document_type:
        query = query.filter_by(document_type=document_type)
    return query.order_by(UploadedDocument.created_at.desc()).all()


def upload(user, file, meta: dict) -> UploadedDocument:
    folder = _folder(user, meta.get("folder_id"))
    saved = storage.save_upload(user.id, file)
    doc = UploadedDocument(user_id=user.id, folder_id=folder.id if folder else None,
                           display_name=(meta.get("display_name") or saved["original_filename"])[:200],
                           document_type=meta.get("document_type", "other"),
                           issued_on=meta.get("issued_on"), expires_on=meta.get("expires_on"), **saved)
    db.session.add(doc)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        storage.delete_file(user.id, saved["stored_filename"])
        raise
    return doc


def update(user, doc_id: int, meta: dict) -> UploadedDocument:
    doc = get_owned(user, doc_id)
    if "folder_id" in meta:
        folder = _folder(user, meta["folder_id"])
        doc.folder_id = folder.id if folder else None
    for key in ("display_name", "document_type", "issued_on", "expires_on"):
        if key in meta:
            setattr(doc, key, meta[key])
    db.session.commit()
    return doc


def delete(user, doc_id: int) -> None:
    doc = get_owned(user, doc_id)
    Achievement.query.filter_by(certificate_document_id=doc.id).update({"certificate_document_id": None})
    stored = doc.stored_filename
    db.session.delete(doc)
    db.session.commit()
    storage.delete_file(user.id, stored)


def create_folder(user, name: str) -> DocumentFolder:
    folder = DocumentFolder(user_id=user.id, name=name.strip())
    db.session.add(folder)
    db.session.commit()
    return folder


def rename_folder(user, folder_id: int, name: str) -> DocumentFolder:
    folder = _folder(user, folder_id)
    folder.name = name.strip()
    db.session.commit()
    return folder


def delete_folder(user, folder_id: int) -> None:
    folder = _folder(user, folder_id)
    UploadedDocument.query.filter_by(folder_id=folder.id).update({"folder_id": None})
    db.session.delete(folder)
    db.session.commit()


def checklist(user, scholarship_id: int | None = None) -> dict:
    """Which required document types the student has (non-expired) vs is missing."""
    today = today_local()
    have = {d.document_type for d in UploadedDocument.query.filter_by(user_id=user.id).all()
            if d.expires_on is None or d.expires_on >= today}
    if scholarship_id:
        sch = db.session.get(Scholarship, scholarship_id)
        if not sch or not sch.is_published:
            raise NotFound("Scholarship not found")
        required = [(r.document_type, r.name, r.is_mandatory) for r in sch.required_documents]
    else:
        tracked = TrackedScholarship.query.filter_by(user_id=user.id).all()
        seen = {}
        for t in tracked:
            for r in t.scholarship.required_documents:
                seen.setdefault(r.document_type, (r.document_type, STANDARD_DOCUMENT_TYPES.get(
                    r.document_type, r.name), r.is_mandatory))
        required = list(seen.values())
    items = [{"document_type": t, "name": n, "is_mandatory": m,
              "available": t != "other" and t in have} for t, n, m in required]
    return {"items": items, "missing": [i for i in items if not i["available"]],
            "document_types": STANDARD_DOCUMENT_TYPES}
