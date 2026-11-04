"""Scholarship search, CRUD, verification, categories and user reports."""
from sqlalchemy import and_, exists, or_

from app.extensions import db
from app.models import (Scholarship, ScholarshipCategory, ScholarshipDocument, ScholarshipEligibility,
                        ScholarshipReport)
from app.services.audit import log_action
from app.utils.errors import BadRequest, Conflict, NotFound
from app.utils.slugs import unique_slug
from app.utils.timeutils import today_local, utcnow

SIMPLE_FIELDS = ("title", "provider_name", "provider_type", "scholarship_type", "category_id", "state",
                 "academic_year", "description", "benefits", "amount_text", "amount_max",
                 "application_open_date", "application_close_date", "official_source_name",
                 "source_url", "application_url", "verification_notes")


def search_query(filters: dict, admin: bool = False):
    query = Scholarship.query
    if not admin:
        query = query.filter(Scholarship.is_published.is_(True))
    if not filters.get("include_expired"):
        query = query.filter(or_(Scholarship.application_close_date.is_(None),
                                 Scholarship.application_close_date >= today_local()))
    if q := filters.get("q"):
        like = f"%{q.strip()}%"
        query = query.filter(or_(Scholarship.title.ilike(like), Scholarship.provider_name.ilike(like),
                                 Scholarship.description.ilike(like)))
    if state := filters.get("state"):
        query = query.filter(or_(Scholarship.state == state, Scholarship.state.is_(None)))
    if filters.get("category_id"):
        query = query.filter(Scholarship.category_id == filters["category_id"])
    if filters.get("scholarship_type"):
        query = query.filter(Scholarship.scholarship_type == filters["scholarship_type"])
    if filters.get("status"):
        query = query.filter(Scholarship.verification_status == filters["status"])
    if filters.get("deadline_before"):
        query = query.filter(Scholarship.application_close_date <= filters["deadline_before"])
    if filters.get("deadline_after"):
        query = query.filter(Scholarship.application_close_date >= filters["deadline_after"])
    E = ScholarshipEligibility
    if level := filters.get("education_level"):
        has_any = exists().where(and_(E.scholarship_id == Scholarship.id, E.criterion_type == "education_level"))
        matches = exists().where(and_(E.scholarship_id == Scholarship.id,
                                      E.criterion_type == "education_level", E.value == level))
        query = query.filter(or_(~has_any, matches))
    if filters.get("income") is not None:
        # Keep schemes with no income cap, or whose cap is >= the student's family income.
        too_low = exists().where(and_(E.scholarship_id == Scholarship.id, E.criterion_type == "income",
                                      E.numeric_value.isnot(None), E.numeric_value < filters["income"]))
        query = query.filter(~too_low)
    sort = filters.get("sort", "deadline")
    if sort == "newest":
        query = query.order_by(Scholarship.created_at.desc())
    elif sort == "title":
        query = query.order_by(Scholarship.title.asc())
    else:
        query = query.order_by(Scholarship.application_close_date.is_(None),
                               Scholarship.application_close_date.asc(), Scholarship.id)
    return query


def get_public(id_or_slug) -> Scholarship:
    query = Scholarship.query.filter(Scholarship.is_published.is_(True))
    sch = query.filter(Scholarship.id == int(id_or_slug)).first() if str(id_or_slug).isdigit() \
        else query.filter(Scholarship.slug == id_or_slug).first()
    if not sch:
        raise NotFound("Scholarship not found")
    return sch


def get_any(sch_id: int) -> Scholarship:
    sch = db.session.get(Scholarship, sch_id)
    if not sch:
        raise NotFound("Scholarship not found")
    return sch


def publish_problems(sch: Scholarship) -> list[str]:
    problems = []
    if not sch.source_url or not sch.application_url or not sch.official_source_name:
        problems.append("Official source name, source URL and application URL are required.")
    if sch.verification_status != "verified" or not sch.last_verified_at:
        problems.append("The record must be verified (with a last-verified date) before publishing.")
    if not sch.eligibility:
        problems.append("At least one eligibility criterion is required.")
    return problems


def _apply(sch: Scholarship, data: dict) -> None:
    if data.get("category_id") and not db.session.get(ScholarshipCategory, data["category_id"]):
        raise BadRequest("Category not found")
    if data.get("application_open_date") and data.get("application_close_date") and \
            data["application_open_date"] > data["application_close_date"]:
        raise BadRequest("Opening date must be before the closing date")
    material_change = any(k in data and getattr(sch, k) != data[k] for k in
                          ("application_close_date", "application_url", "source_url", "amount_text"))
    for key in SIMPLE_FIELDS:
        if key in data:
            setattr(sch, key, data[key])
    if "eligibility" in data:
        sch.eligibility = [ScholarshipEligibility(**e) for e in data["eligibility"]]
        material_change = True
    if "required_documents" in data:
        sch.required_documents = [ScholarshipDocument(**d) for d in data["required_documents"]]
    if material_change and sch.id and sch.verification_status == "verified":
        sch.verification_status = "needs_review"  # edits to key facts require re-verification
        sch.is_published = False


def create(admin, data: dict) -> Scholarship:
    sch = Scholarship(created_by_id=admin.id, verification_status="unverified", is_published=False,
                      slug=unique_slug(Scholarship, f"{data['title']} {data.get('academic_year') or ''}"))
    _apply(sch, data)
    db.session.add(sch)
    db.session.flush()
    log_action(admin, "scholarship.create", "scholarship", sch.id, {"title": sch.title})
    if data.get("is_published"):
        raise BadRequest("New records start unverified. Verify the record before publishing.")
    db.session.commit()
    return sch


def update(admin, sch_id: int, data: dict) -> Scholarship:
    sch = get_any(sch_id)
    _apply(sch, data)
    if "title" in data:
        sch.slug = unique_slug(Scholarship, f"{sch.title} {sch.academic_year or ''}", exclude_id=sch.id)
    if data.get("is_published"):
        if problems := publish_problems(sch):
            db.session.rollback()
            raise BadRequest("Cannot publish this record", details=problems)
        sch.is_published = True
    elif data.get("is_published") is False:
        sch.is_published = False
    log_action(admin, "scholarship.update", "scholarship", sch.id, {"fields": sorted(data)})
    db.session.commit()
    return sch


def verify(admin, sch_id: int, status: str, notes: str | None) -> Scholarship:
    sch = get_any(sch_id)
    if status == "verified" and sch.is_expired:
        raise BadRequest("The deadline has passed. Update the dates from the official source first.")
    sch.verification_status = status
    if notes is not None:
        sch.verification_notes = notes
    if status == "verified":
        sch.last_verified_at, sch.verified_by_id = utcnow(), admin.id
    else:
        sch.is_published = False if status in ("unverified", "needs_review") else sch.is_published
    log_action(admin, "scholarship.verify", "scholarship", sch.id, {"status": status})
    db.session.commit()
    return sch


def delete(admin, sch_id: int) -> None:
    sch = get_any(sch_id)
    log_action(admin, "scholarship.delete", "scholarship", sch.id, {"title": sch.title})
    db.session.delete(sch)
    db.session.commit()


def list_categories():
    return ScholarshipCategory.query.order_by(ScholarshipCategory.name).all()


def save_category(admin, data: dict, cat_id: int | None = None) -> ScholarshipCategory:
    cat = db.session.get(ScholarshipCategory, cat_id) if cat_id else ScholarshipCategory()
    if cat is None:
        raise NotFound("Category not found")
    dup = ScholarshipCategory.query.filter(ScholarshipCategory.name == data["name"].strip(),
                                           ScholarshipCategory.id != (cat_id or 0)).first()
    if dup:
        raise Conflict("A category with this name already exists")
    cat.name, cat.description = data["name"].strip(), data.get("description")
    cat.slug = unique_slug(ScholarshipCategory, cat.name, exclude_id=cat_id)
    db.session.add(cat)
    db.session.flush()
    log_action(admin, "category.update" if cat_id else "category.create", "category", cat.id, {"name": cat.name})
    db.session.commit()
    return cat


def delete_category(admin, cat_id: int) -> None:
    cat = db.session.get(ScholarshipCategory, cat_id)
    if not cat:
        raise NotFound("Category not found")
    log_action(admin, "category.delete", "category", cat.id, {"name": cat.name})
    db.session.delete(cat)
    db.session.commit()


def submit_report(user, sch_id: int, data: dict) -> ScholarshipReport:
    get_public(sch_id)
    report = ScholarshipReport(scholarship_id=sch_id, reporter_id=user.id, **data)
    db.session.add(report)
    db.session.commit()
    return report


def update_report(admin, report_id: int, data: dict) -> ScholarshipReport:
    report = db.session.get(ScholarshipReport, report_id)
    if not report:
        raise NotFound("Report not found")
    report.status = data["status"]
    if "admin_notes" in data:
        report.admin_notes = data["admin_notes"]
    if report.status in ("resolved", "dismissed"):
        report.resolved_by_id, report.resolved_at = admin.id, utcnow()
    log_action(admin, "report.update", "scholarship_report", report.id, {"status": report.status})
    db.session.commit()
    return report
