"""Authoritative marks-based calculations. Never average rounded semester GPAs."""
import ast
import copy
import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models import AcademicPolicy, Semester, Subject, User
from app.services.audit import log_action
from app.utils.errors import Conflict, NotFound, ValidationFailed

DEFAULT_POLICY = {
    "name": "Illustrative 10-point policy — administrator must verify",
    "basis": "percentage",
    "boundary_max": 100,
    "max_point": 10,
    "conversion": "",
    "include_failed": True,
    "bands": [
        {
            "letter": letter,
            "min": low,
            "max": high,
            "point": point,
            "passing": passing,
        }
        for letter, low, high, point, passing in [
            ("F", 0, 40, 0, False),
            ("P", 40, 45, 4, True),
            ("C", 45, 50, 5, True),
            ("B", 50, 60, 6, True),
            ("B+", 60, 70, 7, True),
            ("A", 70, 80, 8, True),
            ("A+", 80, 90, 9, True),
            ("O", 90, 100, 10, True),
        ]
    ],
}
MARK_FIELDS = ("maximum_marks", "passing_marks", "marks_obtained")


def number(value, field, maximum=Decimal("99999999.99")):
    if isinstance(value, bool):
        raise ValidationFailed(f"{field} must be numeric")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationFailed(f"{field} must be numeric")

    if not result.is_finite() or result < 0 or result > maximum:
        raise ValidationFailed(f"{field} is outside its allowed range")
    if result != result.quantize(Decimal("0.01")):
        raise ValidationFailed(
            f"{field} supports at most two decimal places"
        )
    return result


def rounded(value):
    return (
        None
        if value is None
        else float(
            value.quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        )
    )


def convert(expression, gpa, max_point):
    """Restricted affine arithmetic, not Python eval."""
    if not expression or gpa is None:
        return None
    try:
        tree = ast.parse(expression, mode="eval")
        if len(list(ast.walk(tree))) > 40:
            raise ValueError()

        def walk(node):
            if isinstance(node, ast.Expression):
                return walk(node.body)

            if (
                isinstance(node, ast.Name)
                and node.id in {"gpa", "max_point"}
            ):
                return (
                    (Decimal(1), Decimal(0))
                    if node.id == "gpa"
                    else (Decimal(0), Decimal(str(max_point)))
                )

            if (
                isinstance(node, ast.Constant)
                and type(node.value) in (int, float)
            ):
                return Decimal(0), Decimal(str(node.value))

            if (
                isinstance(node, ast.UnaryOp)
                and isinstance(node.op, (ast.UAdd, ast.USub))
            ):
                a, b = walk(node.operand)
                sign = -1 if isinstance(node.op, ast.USub) else 1
                return a * sign, b * sign

            if isinstance(node, ast.BinOp):
                (a, b), (c, d) = walk(node.left), walk(node.right)

                if isinstance(node.op, ast.Add):
                    return a + c, b + d
                if isinstance(node.op, ast.Sub):
                    return a - c, b - d
                if (
                    isinstance(node.op, ast.Mult)
                    and not (a and c)
                ):
                    return a * d + b * c, b * d
                if (
                    isinstance(node.op, ast.Div)
                    and not c
                    and d
                ):
                    return a / d, b / d

            raise ValueError()

        coefficient, constant = walk(tree)
        result = coefficient * gpa + constant
        if not result.is_finite() or abs(result) > 1000000:
            raise ValueError()
        return result

    except (
        SyntaxError,
        ValueError,
        ArithmeticError,
        TypeError,
    ):
        raise ValidationFailed(
            "Invalid conversion: use numbers, gpa, max_point "
            "and + - * / parentheses"
        )


def validate_policy(data):
    if not isinstance(data, dict) or set(data) != set(DEFAULT_POLICY):
        raise ValidationFailed(
            "Supply name, basis, boundary_max, max_point, "
            "conversion, include_failed and bands"
        )

    policy_data = copy.deepcopy(data)

    if (
        not isinstance(policy_data["name"], str)
        or not 1 <= len(policy_data["name"].strip()) <= 150
    ):
        raise ValidationFailed(
            "Policy name is required (maximum 150 characters)"
        )

    if (
        policy_data["basis"] not in ("percentage", "marks")
        or type(policy_data["include_failed"]) is not bool
    ):
        raise ValidationFailed(
            "Invalid boundary basis or failed-subject setting"
        )

    limit = number(
        policy_data["boundary_max"], "Boundary maximum"
    )
    maximum = number(
        policy_data["max_point"],
        "Maximum grade point",
        Decimal("99.99"),
    )

    if (
        limit <= 0
        or maximum <= 0
        or (
            policy_data["basis"] == "percentage"
            and limit != 100
        )
    ):
        raise ValidationFailed(
            "Percentage boundaries must cover 0–100; "
            "maximum point must be positive"
        )

    if (
        not isinstance(policy_data["conversion"], str)
        or len(policy_data["conversion"]) > 120
    ):
        raise ValidationFailed("Conversion expression is too long")

    if (
        not isinstance(policy_data["bands"], list)
        or not 2 <= len(policy_data["bands"]) <= 30
    ):
        raise ValidationFailed(
            "Configure between 2 and 30 grade bands"
        )

    bands = []
    letters = set()
    previous = Decimal(0)
    last_point = Decimal(-1)

    ordered = sorted(
        policy_data["bands"],
        key=lambda band: (
            number(band.get("min"), "Minimum")
            if isinstance(band, dict)
            else Decimal(-1)
        ),
    )

    for band in ordered:
        if (
            not isinstance(band, dict)
            or set(band)
            != {"letter", "min", "max", "point", "passing"}
        ):
            raise ValidationFailed(
                "Each band requires letter, min, max, point and passing"
            )

        label = band["letter"]
        if (
            not isinstance(label, str)
            or not re.fullmatch(r"[A-Za-z0-9+\-]{1,10}", label)
        ):
            raise ValidationFailed(
                "Grade letters must be 1–10 letters, digits, + or -"
            )

        label = label.upper()
        low = number(band["min"], "Minimum")
        high = number(band["max"], "Maximum")
        point = number(band["point"], "Grade point", maximum)

        if (
            label in letters
            or low != previous
            or high <= low
            or point <= last_point
        ):
            raise ValidationFailed(
                "Bands must be unique, contiguous, non-overlapping, "
                "with increasing points"
            )

        if type(band["passing"]) is not bool:
            raise ValidationFailed("Passing must be a boolean")

        letters.add(label)
        bands.append(
            {
                "letter": label,
                "min": float(low),
                "max": float(high),
                "point": float(point),
                "passing": band["passing"],
            }
        )
        previous, last_point = high, point

    if (
        previous != limit
        or last_point != maximum
        or bands[0]["passing"]
        or any(not band["passing"] for band in bands[1:])
    ):
        raise ValidationFailed(
            "Cover the full boundary range, end at maximum point "
            "and configure one lowest failing band"
        )

    policy_data.update(
        bands=bands,
        boundary_max=float(limit),
        max_point=float(maximum),
        name=policy_data["name"].strip(),
    )

    # Validate affine conversion at both ends of the full GPA range.
    for value in (Decimal(0), maximum):
        convert(policy_data["conversion"], value, maximum)

    return policy_data


def policy(lock=False):
    query = AcademicPolicy.query.filter_by(id=1)
    row = (
        query.with_for_update(read=True).first()
        if lock
        else query.first()
    )
    return {
        "version": row.version if row else 0,
        "configuration": copy.deepcopy(
            row.configuration if row else DEFAULT_POLICY
        ),
    }


def update_policy(user, body):
    if (
        not isinstance(body, dict)
        or type(body.get("version")) is not int
    ):
        raise ValidationFailed("Policy version is required")

    configuration = validate_policy(body.get("configuration"))
    row = (
        AcademicPolicy.query.filter_by(id=1)
        .with_for_update()
        .first()
    )
    if body["version"] != (row.version if row else 0):
        raise Conflict(
            "Grading policy changed. Reload before saving."
        )

    if row is None:
        row = AcademicPolicy(id=1, version=0)
        db.session.add(row)

    row.configuration = configuration
    row.version += 1

    log_action(
        user,
        "academic_policy.update",
        "academic_policy",
        1,
        {
            "version": row.version,
            "configuration": configuration,
        },
    )
    db.session.commit()
    return policy()


def evaluate(subject, configuration):
    result = {
        "id": subject.id,
        "name": subject.name,
        "code": subject.code,
        "credits": float(subject.credits),
        "version": subject.record_version,
        **{
            field: (
                float(getattr(subject, field))
                if getattr(subject, field) is not None
                else None
            )
            for field in MARK_FIELDS
        },
        "grade": None,
        "grade_point": None,
        "result": "Incomplete",
        "included": False,
        "legacy_grade": (
            subject.grade_label
            if not subject.master_managed
            else None
        ),
    }

    if not subject.master_managed:
        result["result"] = "Historical — marks unavailable"
        return result

    if any(result[field] is None for field in MARK_FIELDS):
        return result

    maximum, minimum, obtained = (
        getattr(subject, field) for field in MARK_FIELDS
    )

    if (
        maximum <= 0
        or minimum > maximum
        or obtained > maximum
        or min(minimum, obtained) < 0
        or subject.credits <= 0
        or (
            configuration["basis"] == "marks"
            and maximum
            > Decimal(str(configuration["boundary_max"]))
        )
    ):
        result["result"] = "Invalid"
        return result

    value = (
        obtained * 100 / maximum
        if configuration["basis"] == "percentage"
        else obtained
    )

    band = next(
        (
            candidate
            for candidate in configuration["bands"]
            if (
                Decimal(str(candidate["min"]))
                <= value
                < Decimal(str(candidate["max"]))
            )
            or (
                value
                == Decimal(str(configuration["boundary_max"]))
                == Decimal(str(candidate["max"]))
            )
        ),
        None,
    )

    if band is None:
        result["result"] = "Invalid"
        return result

    if obtained < minimum:
        band = configuration["bands"][0]

    passed = band["passing"] and obtained >= minimum
    result.update(
        grade=band["letter"],
        grade_point=band["point"],
        result="Pass" if passed else "Fail",
        included=passed or configuration["include_failed"],
    )
    return result


def aggregate(subjects, configuration):
    valid = [
        subject
        for subject in subjects
        if subject["result"] in ("Pass", "Fail")
    ]
    included = [
        subject for subject in valid if subject["included"]
    ]

    credits = sum(
        (
            Decimal(str(subject["credits"]))
            for subject in included
        ),
        Decimal(0),
    )
    points = sum(
        (
            Decimal(str(subject["credits"]))
            * Decimal(str(subject["grade_point"]))
            for subject in included
        ),
        Decimal(0),
    )
    gpa = points / credits if credits else None

    maximum = sum(
        (
            Decimal(str(subject["maximum_marks"]))
            for subject in valid
        ),
        Decimal(0),
    )
    marks = sum(
        (
            Decimal(str(subject["marks_obtained"]))
            for subject in valid
        ),
        Decimal(0),
    )

    grade = next(
        (
            band["letter"]
            for band in reversed(configuration["bands"])
            if gpa is not None
            and gpa >= Decimal(str(band["point"]))
        ),
        None,
    )

    return {
        "gpa": rounded(gpa),
        "grade": grade,
        "total_credits": rounded(credits),
        "completed_credits": rounded(
            sum(
                (
                    Decimal(str(subject["credits"]))
                    for subject in valid
                    if subject["result"] == "Pass"
                ),
                Decimal(0),
            )
        ),
        "raw_percentage": (
            rounded(marks * 100 / maximum)
            if maximum
            else None
        ),
        "converted_percentage": rounded(
            convert(
                configuration["conversion"],
                gpa,
                configuration["max_point"],
            )
        ),
        "excluded_subjects": len(subjects) - len(included),
        "pending_subjects": len(subjects) - len(valid),
        "failed_subjects": sum(
            subject["result"] == "Fail" for subject in valid
        ),
    }


def dashboard(user):
    current_policy = policy()
    configuration = current_policy["configuration"]

    records = (
        Semester.query.options(selectinload(Semester.subjects))
        .filter_by(user_id=user.id)
        .all()
    )
    by_number = {semester.number: semester for semester in records}
    semesters = []
    all_subjects = []

    for number_value in range(1, 9):
        semester = by_number.get(number_value)
        subjects = (
            [
                evaluate(subject, configuration)
                for subject in semester.subjects
            ]
            if semester
            else []
        )
        all_subjects.extend(subjects)
        result = aggregate(subjects, configuration)

        semesters.append(
            {
                "number": number_value,
                "academic_year": (
                    semester.academic_year if semester else ""
                ),
                "subjects": subjects,
                **result,
                "sgpa": result["gpa"],
                "cumulative": aggregate(
                    all_subjects, configuration
                ),
                "completed": bool(subjects)
                and all(
                    subject["result"] == "Pass"
                    for subject in subjects
                ),
            }
        )

    profile = user.profile
    return {
        "policy": current_policy,
        "student": {
            "name": (
                profile.full_name if profile else user.email
            ),
            "student_id": user.id,
            "course": profile.degree if profile else None,
            "department": profile.branch if profile else None,
        },
        "semesters": semesters,
        "total": {
            **aggregate(all_subjects, configuration),
            "completed_semesters": sum(
                semester["completed"] for semester in semesters
            ),
        },
    }


def own_semester(user, number_value, create=False):
    if number_value not in range(1, 9):
        raise NotFound("Semester must be between 1 and 8")

    semester = Semester.query.filter_by(
        user_id=user.id, number=number_value
    ).first()

    if semester is None and create:
        semester = Semester(
            user_id=user.id, number=number_value
        )
        db.session.add(semester)
        db.session.flush()

    return semester


def save_subject(user, number_value, body, subject_id=None):
    allowed = {
        "name",
        "code",
        "credits",
        "version",
        *MARK_FIELDS,
    }
    if (
        not isinstance(body, dict)
        or set(body) - allowed
    ):
        raise ValidationFailed("Invalid subject payload")

    # Serialize writes for this student, including first-semester creation.
    User.query.filter_by(id=user.id).with_for_update().one()
    configuration = policy(lock=True)["configuration"]

    semester = own_semester(
        user, number_value, create=subject_id is None
    )
    subject = (
        Subject.query.filter_by(
            id=subject_id, semester_id=semester.id
        ).first()
        if subject_id and semester
        else None
    )

    if subject_id and subject is None:
        raise NotFound("Subject not found")

    if subject is not None and (
        type(body.get("version")) is not int
        or body["version"] != subject.record_version
    ):
        raise Conflict(
            "Subject changed. Reload before saving."
        )

    name = body.get("name")
    code = body.get("code")

    if (
        not isinstance(name, str)
        or not 1 <= len(name.strip()) <= 200
    ):
        raise ValidationFailed(
            "Subject name is required (maximum 200 characters)"
        )

    if code is not None and (
        not isinstance(code, str)
        or len(code.strip()) > 30
        or re.search(r"[\x00-\x1f]", code)
    ):
        raise ValidationFailed(
            "Course code must be at most 30 printable characters"
        )

    code = (code or "").strip().upper() or None

    if code and Subject.query.filter(
        Subject.semester_id == semester.id,
        db.func.upper(Subject.code) == code,
        Subject.id != (subject_id or 0),
    ).first():
        raise Conflict(
            "This course code already exists in this semester"
        )

    credits = number(
        body.get("credits"),
        "Credits",
        Decimal("999.99"),
    )
    if credits <= 0:
        raise ValidationFailed("Credits must be positive")

    marks = {
        field: (
            number(body[field], field)
            if body.get(field) is not None
            else None
        )
        for field in MARK_FIELDS
    }
    maximum = marks["maximum_marks"]

    if maximum is not None and (
        maximum <= 0
        or any(
            marks[field] is not None
            and marks[field] > maximum
            for field in MARK_FIELDS[1:]
        )
    ):
        raise ValidationFailed(
            "Maximum must be positive; passing and obtained "
            "marks cannot exceed maximum"
        )

    if (
        configuration["basis"] == "marks"
        and maximum is not None
        and maximum
        > Decimal(str(configuration["boundary_max"]))
    ):
        raise ValidationFailed(
            "Maximum marks exceed the configured marks boundary"
        )

    if subject is None:
        subject = Subject(
            semester_id=semester.id,
            record_version=0,
        )
        db.session.add(subject)

    subject.name = name.strip()
    subject.code = code
    subject.credits = credits

    for field, value in marks.items():
        setattr(subject, field, value)

    subject.master_managed = True
    subject.record_version += 1

    result = evaluate(subject, configuration)
    subject.grade_label = result["grade"] or ""
    subject.grade_point = result["grade_point"] or 0
    subject.counts_in_gpa = result["included"]

    db.session.commit()
    return dashboard(user)


def delete_subject(user, number_value, subject_id, version):
    User.query.filter_by(id=user.id).with_for_update().one()
    semester = own_semester(user, number_value)

    subject = (
        Subject.query.filter_by(
            id=subject_id, semester_id=semester.id
        ).first()
        if semester
        else None
    )

    if subject is None:
        raise NotFound("Subject not found")

    if (
        type(version) is not int
        or subject.record_version != version
    ):
        raise Conflict(
            "Subject changed. Reload before deleting."
        )

    db.session.delete(subject)
    db.session.commit()
    return dashboard(user)
