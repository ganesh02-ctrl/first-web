from flask import Blueprint, request, send_file
from flask_jwt_extended import current_user

from app.middleware.auth import login_required
from app.routes.helpers import form_data, int_arg, json_body
from app.schemas import load
from app.schemas.document import DocumentMetaSchema, FolderSchema
from app.services import document as svc
from app.services import storage
from app.utils.constants import STANDARD_DOCUMENT_TYPES
from app.utils.errors import NotFound, UnsupportedMedia
from app.utils.responses import success

bp = Blueprint("documents", __name__, url_prefix="/api/documents")


@bp.get("")
@login_required
def list_documents():
    docs = svc.list_documents(current_user, int_arg("folder_id"), request.args.get("document_type"))
    return success([d.to_dict() for d in docs])


@bp.post("")
@login_required
def upload():
    meta = load(DocumentMetaSchema(), form_data())
    doc = svc.upload(current_user, request.files.get("file"), meta)
    return success(doc.to_dict(), "Document uploaded", 201)


@bp.patch("/<int:doc_id>")
@login_required
def update(doc_id):
    doc = svc.update(current_user, doc_id, load(DocumentMetaSchema(), json_body(), partial=True))
    return success(doc.to_dict(), "Document updated")


@bp.delete("/<int:doc_id>")
@login_required
def delete(doc_id):
    svc.delete(current_user, doc_id)
    return success(None, "Document deleted")


def _send(doc_id: int, attachment: bool):
    doc = svc.get_owned(current_user, doc_id)
    if not attachment and not doc.previewable:
        raise UnsupportedMedia("Preview is not available for this file type")
    path = storage.file_path(current_user.id, doc.stored_filename)
    if not path.exists():
        raise NotFound("The file is missing from storage")
    return send_file(path, mimetype=doc.mime_type, as_attachment=attachment,
                     download_name=doc.original_filename, max_age=0)


@bp.get("/<int:doc_id>/download")
@login_required
def download(doc_id):
    return _send(doc_id, attachment=True)


@bp.get("/<int:doc_id>/preview")
@login_required
def preview(doc_id):
    return _send(doc_id, attachment=False)


@bp.get("/folders")
@login_required
def folders():
    return success([f.to_dict() for f in current_user.folders])


@bp.post("/folders")
@login_required
def create_folder():
    folder = svc.create_folder(current_user, load(FolderSchema(), json_body())["name"])
    return success(folder.to_dict(), "Folder created", 201)


@bp.patch("/folders/<int:folder_id>")
@login_required
def rename_folder(folder_id):
    folder = svc.rename_folder(current_user, folder_id, load(FolderSchema(), json_body())["name"])
    return success(folder.to_dict(), "Folder renamed")


@bp.delete("/folders/<int:folder_id>")
@login_required
def delete_folder(folder_id):
    svc.delete_folder(current_user, folder_id)
    return success(None, "Folder deleted; its documents were kept")


@bp.get("/checklist")
@login_required
def checklist():
    return success(svc.checklist(current_user, int_arg("scholarship_id")))


@bp.get("/types")
@login_required
def types():
    return success(STANDARD_DOCUMENT_TYPES)
