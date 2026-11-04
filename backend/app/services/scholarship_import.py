"""CSV import. Imported rows are ALWAYS created unverified and unpublished; an admin must verify them.

Columns (header row required):
title, provider_name, provider_type, scholarship_type, category, state, academic_year, description,
benefits, amount_text, amount_max, application_open_date, application_close_date,
official_source_name, source_url, application_url, eligibility, required_documents

eligibility:        JSON list, e.g. [{"criterion_type":"income","numeric_value":250000,"description":"..."}]
required_documents: JSON list, e.g. [{"document_type":"income_certificate","name":"Income Certificate"}]
Rows are matched on (title, provider_name, academic_year); matches are updated and set to needs_review.
"""
import csv
import io
import json

from marshmallow import ValidationError

from app.extensions import db
from app.models import Scholarship, ScholarshipCategory
from app.schemas.scholarship import ScholarshipSchema
from app.services.audit import log_action
from app.services.scholarship import _apply
from app.utils.errors import BadRequest
from app.utils.slugs import unique_slug

REQUIRED_COLUMNS = {"title", "provider_name", "provider_type", "scholarship_type",
                    "official_source_name", "source_url", "application_url"}
MAX_ROWS = 2000


def _row_to_payload(row: dict) -> dict:
    payload = {k: (v.strip() if isinstance(v, str) else v) for k, v in row.items() if k}
    payload = {k: v for k, v in payload.items() if v not in ("", None)}
    for key in ("eligibility", "required_documents"):
        if key in payload:
            payload[key] = json.loads(payload[key])
    category = payload.pop("category", None)
    if category:
        cat = ScholarshipCategory.query.filter_by(name=category).first()
        if not cat:
            raise ValueError(f"Unknown category '{category}'")
        payload["category_id"] = cat.id
    return payload


def import_csv(admin, raw: bytes, dry_run: bool = False) -> dict:
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise BadRequest("CSV must be UTF-8 encoded")
    reader = csv.DictReader(io.StringIO(text))
    missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
    if missing:
        raise BadRequest(f"Missing required columns: {', '.join(sorted(missing))}")
    schema = ScholarshipSchema()
    created = updated = 0
    errors = []
    for index, row in enumerate(reader, start=2):
        if index - 1 > MAX_ROWS:
            errors.append({"row": index, "errors": f"Row limit of {MAX_ROWS} reached"})
            break
        try:
            data = schema.load(_row_to_payload(row))
        except ValidationError as exc:
            errors.append({"row": index, "errors": exc.messages})
            continue
        except ValueError as exc:  # json.JSONDecodeError and unknown category
            errors.append({"row": index, "errors": str(exc)})
            continue
        data.pop("is_published", None)
        existing = Scholarship.query.filter_by(title=data["title"], provider_name=data["provider_name"],
                                               academic_year=data.get("academic_year")).first()
        try:
            with db.session.begin_nested():
                if existing:
                    _apply(existing, data)
                    existing.verification_status, existing.is_published = "needs_review", False
                    updated += 1
                else:
                    sch = Scholarship(created_by_id=admin.id, verification_status="unverified",
                                      is_published=False,
                                      slug=unique_slug(Scholarship, f"{data['title']} {data.get('academic_year') or ''}"))
                    _apply(sch, data)
                    db.session.add(sch)
                    db.session.flush()
                    created += 1
        except Exception as exc:  # noqa: BLE001 - report per-row failure
            errors.append({"row": index, "errors": getattr(exc, "message", None) or str(exc)[:300]})
    summary = {"created": created, "updated": updated, "errors": errors, "dry_run": dry_run}
    if dry_run:
        db.session.rollback()
    else:
        log_action(admin, "scholarship.import_csv", "scholarship", None,
                   {"created": created, "updated": updated, "errors": len(errors)})
        db.session.commit()
    return summary
