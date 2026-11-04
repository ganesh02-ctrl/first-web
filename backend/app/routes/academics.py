import io

from flask import Blueprint, send_file
from flask_jwt_extended import current_user
from marshmallow import fields, validate

from app.middleware.auth import login_required
from app.routes.helpers import json_body
from app.schemas import load
from app.schemas.academic import GradingScaleSchema, SemesterSchema, SubjectSchema
from app.schemas.common import BaseSchema
from app.services import academic as svc
from app.services.report_pdf import academic_report
from app.utils.responses import success

bp = Blueprint("academics", __name__, url_prefix="/api/academics")


class CalculateSchema(BaseSchema):
    grading_scale_id = fields.Integer(required=True)
    subjects = fields.List(fields.Nested(SubjectSchema(only=("credits", "grade_label"))), required=True,
                           validate=validate.Length(min=1, max=60))


@bp.get("/scales")
@login_required
def scales():
    return success([s.to_dict() for s in svc.visible_scales(current_user)])


@bp.post("/scales")
@login_required
def create_scale():
    body = json_body()
    data = load(GradingScaleSchema(), body)
    data["as_template"] = bool(current_user.is_admin and (body or {}).get("as_template"))
    return success(svc.save_scale(current_user, data).to_dict(), "Grading scale saved", 201)


@bp.put("/scales/<int:scale_id>")
@login_required
def update_scale(scale_id):
    data = load(GradingScaleSchema(), json_body())
    return success(svc.save_scale(current_user, data, scale_id).to_dict(), "Grading scale updated")


@bp.delete("/scales/<int:scale_id>")
@login_required
def delete_scale(scale_id):
    svc.delete_scale(current_user, scale_id)
    return success(None, "Grading scale deleted")


@bp.get("/semesters")
@login_required
def semesters():
    return success([s.to_dict() for s in current_user.semesters])


@bp.post("/semesters")
@login_required
def create_semester():
    sem = svc.save_semester(current_user, load(SemesterSchema(), json_body()))
    return success(sem.to_dict(), "Semester created", 201)


@bp.get("/semesters/<int:sem_id>")
@login_required
def get_semester(sem_id):
    return success(svc.get_semester(current_user, sem_id).to_dict())


@bp.put("/semesters/<int:sem_id>")
@login_required
def update_semester(sem_id):
    sem = svc.save_semester(current_user, load(SemesterSchema(), json_body(), partial=True), sem_id)
    return success(sem.to_dict(), "Semester updated")


@bp.delete("/semesters/<int:sem_id>")
@login_required
def delete_semester(sem_id):
    svc.delete_semester(current_user, sem_id)
    return success(None, "Semester deleted")


@bp.post("/semesters/<int:sem_id>/subjects")
@login_required
def add_subject(sem_id):
    svc.save_subject(current_user, sem_id, load(SubjectSchema(), json_body()))
    return success(svc.get_semester(current_user, sem_id).to_dict(), "Subject added", 201)


@bp.put("/semesters/<int:sem_id>/subjects/<int:subject_id>")
@login_required
def update_subject(sem_id, subject_id):
    svc.save_subject(current_user, sem_id, load(SubjectSchema(), json_body(), partial=True), subject_id)
    return success(svc.get_semester(current_user, sem_id).to_dict(), "Subject updated")


@bp.delete("/semesters/<int:sem_id>/subjects/<int:subject_id>")
@login_required
def delete_subject(sem_id, subject_id):
    svc.delete_subject(current_user, sem_id, subject_id)
    return success(svc.get_semester(current_user, sem_id).to_dict(), "Subject deleted")


@bp.get("/summary")
@login_required
def summary():
    return success(svc.summary(current_user))


@bp.post("/calculate")
@login_required
def calculate():
    data = load(CalculateSchema(), json_body())
    return success(svc.calculate_preview(current_user, data["grading_scale_id"], data["subjects"]))


@bp.get("/report.pdf")
@login_required
def report_pdf():
    return send_file(io.BytesIO(academic_report(current_user)), mimetype="application/pdf",
                     as_attachment=True, download_name="academic-report.pdf")
