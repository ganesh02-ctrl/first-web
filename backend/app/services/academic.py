
"""Grading scales, semesters, subjects and GPA summaries."""
from sqlalchemy import or_

from app.extensions import db
from app.models import GradeMapping, GradingScale, Semester, Subject
from app.services.audit import log_action
from app.utils.errors import BadRequest, Conflict, Forbidden, NotFound
from app.utils.gpa import calculate_cgpa


DEFAULT_SCALE_NAME = "VTU B.E./B.Tech – 2022 Scheme"


def default_grading_scale() -> GradingScale:
    """Return the earliest shared 2022 VTU template."""
    scale = (
        GradingScale.query
        .filter(
            GradingScale.is_template.is_(True),
            GradingScale.name == DEFAULT_SCALE_NAME,
        )
        .order_by(GradingScale.id.asc())
        .first()
    )

    if not scale:
        raise BadRequest(
            "The default 2022 VTU grading scale is not configured. "
            "Ask an administrator to import the shared template."
        )

    return scale


def visible_scales(user):
    return (
        GradingScale.query
        .filter(
            or_(
                GradingScale.is_template.is_(True),
                GradingScale.owner_user_id == user.id,
            )
        )
        .order_by(GradingScale.is_template.desc(), GradingScale.name)
        .all()
    )


def get_visible_scale(user, scale_id: int) -> GradingScale:
    scale = db.session.get(GradingScale, scale_id)
    if not scale or not (
        scale.is_template or scale.owner_user_id == user.id
    ):
        raise NotFound("Grading scale not found")
    return scale


def save_scale(user, data: dict, scale_id: int | None = None) -> GradingScale:
    as_template = user.is_admin and data.pop("as_template", False)

    if scale_id:
        scale = get_visible_scale(user, scale_id)
        if scale.is_template and not user.is_admin or (
            not scale.is_template and scale.owner_user_id != user.id
        ):
            raise Forbidden("You cannot edit this grading scale")
    else:
        scale = GradingScale(
            owner_user_id=None if as_template else user.id,
            is_template=bool(as_template),
        )
        db.session.add(scale)

    scale.name = data["name"]
    scale.description = data.get("description")
    scale.max_grade_point = data["max_grade_point"]

    if scale.id is not None and scale.grades:
        scale.grades.clear()
        db.session.flush()

    scale.grades = [
        GradeMapping(**{**g, "label": g["label"].strip().upper()})
        for g in data["grades"]
    ]

    db.session.flush()

    if scale.is_template:
        log_action(
            user,
            "grading_scale.save",
            "grading_scale",
            scale.id,
            {"name": scale.name},
        )

    db.session.commit()
    return scale


def delete_scale(user, scale_id: int) -> None:
    scale = get_visible_scale(user, scale_id)

    if (scale.is_template and not user.is_admin) or (
        not scale.is_template and scale.owner_user_id != user.id
    ):
        raise Forbidden("You cannot delete this grading scale")

    if Semester.query.filter_by(grading_scale_id=scale.id).first() and not scale.is_template:
        raise Conflict("This scale is used by a semester. Change those semesters first.")

    db.session.delete(scale)
    db.session.commit()


def get_semester(user, sem_id: int) -> Semester:
    sem = Semester.query.filter_by(id=sem_id, user_id=user.id).first()
    if not sem:
        raise NotFound("Semester not found")
    return sem


def save_semester(user, data: dict, sem_id: int | None = None) -> Semester:
    if sem_id:
        sem = get_semester(user, sem_id)

        # On updates, preserve the existing scale unless a new one is supplied.
        if "grading_scale_id" in data:
            scale_id = data.get("grading_scale_id")
            scale = (
                get_visible_scale(user, scale_id)
                if scale_id
                else default_grading_scale()
            )
        else:
            scale = None
    else:
        sem = Semester(user_id=user.id)

        # New semesters use the selected scale, or the shared 2022 default.
        scale_id = data.get("grading_scale_id")
        scale = (
            get_visible_scale(user, scale_id)
            if scale_id
            else default_grading_scale()
        )

    if "number" in data:
        clash = Semester.query.filter(
            Semester.user_id == user.id,
            Semester.number == data["number"],
            Semester.id != (sem_id or 0),
        ).first()

        if clash:
            raise Conflict(f"Semester {data['number']} already exists")

    for key in ("number", "title", "academic_year", "notes"):
        if key in data:
            setattr(sem, key, data[key])

    if scale and sem.grading_scale_id != scale.id:
        if sem.subjects:
            _regrade(sem.subjects, scale)
        sem.grading_scale_id = scale.id

    db.session.add(sem)
    db.session.commit()
    return sem


def _mapping(scale: GradingScale, label: str) -> GradeMapping:
    wanted = label.strip().upper()

    for grade in scale.grades:
        if grade.label == wanted:
            return grade

    raise BadRequest(
        f"Grade '{label}' is not in the scale '{scale.name}'. "
        f"Valid grades: {', '.join(g.label for g in scale.grades)}"
    )


def _regrade(subjects, scale) -> None:
    for subject in subjects:
        grade = _mapping(scale, subject.grade_label)
        subject.grade_point = grade.grade_point
        subject.counts_in_gpa = grade.counts_in_gpa


def delete_semester(user, sem_id: int) -> None:
    db.session.delete(get_semester(user, sem_id))
    db.session.commit()


def save_subject(
    user,
    sem_id: int,
    data: dict,
    subject_id: int | None = None,
) -> Subject:
    sem = get_semester(user, sem_id)

    if not sem.grading_scale:
        raise BadRequest("Assign a grading scale to this semester first")

    subject = (
        Subject.query.filter_by(id=subject_id, semester_id=sem.id).first()
        if subject_id
        else Subject(semester_id=sem.id)
    )

    if subject is None:
        raise NotFound("Subject not found")

    for key in ("name", "code", "credits"):
        if key in data:
            setattr(subject, key, data[key])

    if "grade_label" in data:
        grade = _mapping(sem.grading_scale, data["grade_label"])
        subject.grade_label = grade.label
        subject.grade_point = grade.grade_point
        subject.counts_in_gpa = grade.counts_in_gpa

    db.session.add(subject)
    db.session.commit()
    return subject


def delete_subject(user, sem_id: int, subject_id: int) -> None:
    sem = get_semester(user, sem_id)
    subject = Subject.query.filter_by(
        id=subject_id,
        semester_id=sem.id,
    ).first()

    if not subject:
        raise NotFound("Subject not found")

    db.session.delete(subject)
    db.session.commit()


def summary(user) -> dict:
    semesters = (
        Semester.query
        .filter_by(user_id=user.id)
        .order_by(Semester.number)
        .all()
    )

    result = calculate_cgpa(semesters)
    scale_maxes = {
        float(s.grading_scale.max_grade_point)
        for s in semesters
        if s.grading_scale
    }

    return {
        "cgpa": float(result.gpa) if result.gpa is not None else None,
        "total_credits": float(result.total_credits),
        "semester_count": len(semesters),
        "mixed_scales": len(scale_maxes) > 1,
        "max_grade_point": scale_maxes.pop() if len(scale_maxes) == 1 else None,
        "semesters": [
            s.to_dict(include_subjects=False) for s in semesters
        ],
    }


def calculate_preview(user, scale_id: int, subjects: list[dict]) -> dict:
    """Stateless SGPA calculation using a visible grading scale."""
    from app.utils.gpa import GradedItem, weighted_gpa

    scale = get_visible_scale(user, scale_id)
    items = []

    for subject in subjects:
        grade = _mapping(scale, subject["grade_label"])
        items.append(
            GradedItem(
                subject["credits"],
                grade.grade_point,
                grade.counts_in_gpa,
            )
        )

    return weighted_gpa(items).as_dict()
