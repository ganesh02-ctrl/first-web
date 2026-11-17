"""JWT-protected Master Semester Records API."""
from io import BytesIO

from flask import Blueprint, request, send_file
from flask_jwt_extended import current_user

from app.middleware.auth import (
    admin_required,
    login_required,
    student_required,
)
from app.services import master as service
from app.services.master_report import excel_report, pdf_report
from app.utils.responses import success

bp = Blueprint(
    "master_semesters",
    __name__,
    url_prefix="/api/master-semesters",
)


@bp.get("")
@student_required
def records():
    return success(service.dashboard(current_user))


@bp.get("/policy")
@login_required
def policy():
    return success(service.policy())


@bp.put("/policy")
@admin_required
def update_policy():
    return success(
        service.update_policy(
            current_user, request.get_json(silent=True)
        ),
        "Grading policy updated",
    )


@bp.post("/<int:number>/subjects")
@student_required
def add_subject(number):
    return success(
        service.save_subject(
            current_user,
            number,
            request.get_json(silent=True),
        ),
        "Subject saved",
        201,
    )


@bp.put("/<int:number>/subjects/<int:subject_id>")
@student_required
def edit_subject(number, subject_id):
    return success(
        service.save_subject(
            current_user,
            number,
            request.get_json(silent=True),
            subject_id,
        ),
        "Subject updated",
    )


@bp.delete("/<int:number>/subjects/<int:subject_id>")
@student_required
def delete_subject(number, subject_id):
    body = request.get_json(silent=True)
    version = (
        body.get("version") if isinstance(body, dict) else None
    )
    return success(
        service.delete_subject(
            current_user, number, subject_id, version
        ),
        "Subject deleted",
    )


@bp.get("/report.pdf")
@student_required
def pdf():
    return send_file(
        BytesIO(pdf_report(service.dashboard(current_user))),
        mimetype="application/pdf",
        as_attachment=True,
        download_name="master-semester-report.pdf",
    )


@bp.get("/report.xlsx")
@student_required
def excel():
    return send_file(
        BytesIO(excel_report(service.dashboard(current_user))),
        mimetype=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        as_attachment=True,
        download_name="master-semester-report.xlsx",
    )
