"""Private file storage: extension + content sniffing, size limit, random names, safe paths."""
import hashlib
import os
import uuid
from pathlib import Path

import filetype
from flask import current_app
from werkzeug.datastructures import FileStorage

from app.utils.errors import BadRequest, UnsupportedMedia

MIME_BY_EXT = {"pdf": "application/pdf", "png": "image/png", "jpg": "image/jpeg",
               "jpeg": "image/jpeg", "webp": "image/webp"}


def _root() -> Path:
    return Path(current_app.config["UPLOAD_FOLDER"]).resolve()


def _user_dir(user_id: int) -> Path:
    path = _root() / str(int(user_id))
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_upload(user_id: int, file: FileStorage) -> dict:
    if file is None or not file.filename:
        raise BadRequest("No file was uploaded")
    original = os.path.basename(file.filename.replace("\\", "/"))[:255]
    ext = original.rsplit(".", 1)[-1].lower() if "." in original else ""
    allowed = current_app.config["ALLOWED_UPLOAD_EXTENSIONS"]
    if ext not in allowed or ext not in MIME_BY_EXT:
        raise UnsupportedMedia(f"File type not allowed. Allowed: {', '.join(sorted(allowed))}")
    data = file.read()
    max_bytes = current_app.config["MAX_UPLOAD_MB"] * 1024 * 1024
    if not data:
        raise BadRequest("The uploaded file is empty")
    if len(data) > max_bytes:
        raise BadRequest(f"File too large. Maximum size is {current_app.config['MAX_UPLOAD_MB']} MB.",
                         status=413, code="payload_too_large")
    kind = filetype.guess(data[:8192])
    expected = MIME_BY_EXT[ext]
    if kind is None or kind.mime != expected:
        raise UnsupportedMedia("File content does not match its extension")
    stored = f"{uuid.uuid4().hex}.{'jpg' if ext == 'jpeg' else ext}"
    (_user_dir(user_id) / stored).write_bytes(data)
    return {"original_filename": original, "stored_filename": stored, "mime_type": expected,
            "size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def file_path(user_id: int, stored_filename: str) -> Path:
    path = (_root() / str(int(user_id)) / stored_filename).resolve()
    if _root() not in path.parents:
        raise BadRequest("Invalid file path")
    return path


def delete_file(user_id: int, stored_filename: str) -> None:
    try:
        file_path(user_id, stored_filename).unlink(missing_ok=True)
    except OSError:
        current_app.logger.warning("Could not delete %s", stored_filename)
