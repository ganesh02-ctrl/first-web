"""SQLite integration tests by default; fixtures are never application records."""
from copy import deepcopy
from decimal import Decimal
from io import BytesIO

import pytest
from openpyxl import load_workbook
from pypdf import PdfReader

from app.extensions import db
from app.models import GradingScale, Semester, Subject
from app.services.master import DEFAULT_POLICY, convert

try:
    from conftest import login_headers
except ImportError:
    from tests.conftest import login_headers

ROOT = "/api/master-semesters"
SUBJECT = {
    "name": "Calculus",
    "code": "MA101",
    "credits": 4,
    "maximum_marks": 100,
    "passing_marks": 40,
    "marks_obtained": 90,
}


def get_data(client, headers):
    response = client.get(ROOT, headers=headers)
    assert response.status_code == 200, response.get_json()
    return response.get_json()["data"]


def add(client, headers, semester=1, **values):
    response = client.post(
        f"{ROOT}/{semester}/subjects",
        headers=headers,
        json={**SUBJECT, **values},
    )
    assert response.status_code == 201, response.get_json()
    return response.get_json()["data"]


def configure(client, headers, **patch):
    current = client.get(
        f"{ROOT}/policy", headers=headers
    ).get_json()["data"]
    current["configuration"].update(patch)

    response = client.put(
        f"{ROOT}/policy",
        headers=headers,
        json=current,
    )
    assert response.status_code == 200, response.get_json()
    return response.get_json()["data"]


def test_eight_empty_semesters(client, student_headers):
    data = get_data(client, student_headers)
    assert [
        semester["number"]
        for semester in data["semesters"]
    ] == list(range(1, 9))

    assert all(
        semester["sgpa"] is None
        for semester in data["semesters"]
    )
    assert data["total"]["gpa"] is None
    assert data["total"]["completed_semesters"] == 0


def test_weighted_crud_cumulative_percentages(
    client, student_headers
):
    add(client, student_headers)

    add(
        client,
        student_headers,
        code="LAB",
        credits=2,
        maximum_marks=50,
        passing_marks=20,
        marks_obtained=35,
    )

    data = add(
        client,
        student_headers,
        semester=2,
        code="CS201",
        credits=1,
        marks_obtained=50,
    )

    assert data["semesters"][0]["sgpa"] == 9.33
    assert (
        data["semesters"][0]["raw_percentage"]
        == 83.33
    )
    assert data["total"]["gpa"] == 8.86
    assert data["total"]["raw_percentage"] == 70
    assert data["total"]["completed_semesters"] == 2

    first = data["semesters"][0]["subjects"][0]
    body = {
        **SUBJECT,
        "marks_obtained": 40,
        "credits": 3,
        "version": first["version"],
    }
    url = f"{ROOT}/1/subjects/{first['id']}"

    response = client.put(
        url, headers=student_headers, json=body
    )
    assert response.status_code == 200

    updated = response.get_json()["data"]
    assert updated["total"]["gpa"] == 5.67
    assert all(
        semester["cumulative"]["gpa"] == 5.67
        for semester in updated["semesters"][1:]
    )

    assert client.put(
        url, headers=student_headers, json=body
    ).status_code == 409

    assert client.delete(
        url,
        headers=student_headers,
        json={"version": first["version"]},
    ).status_code == 409

    assert client.delete(
        url,
        headers=student_headers,
        json={"version": 2},
    ).status_code == 200

    assert get_data(
        client, student_headers
    )["semesters"][0]["sgpa"] == 8


@pytest.mark.parametrize(
    "patch",
    [
        {"name": " "},
        {"credits": 0},
        {"credits": -1},
        {"credits": "NaN"},
        {"credits": True},
        {"credits": 1.001},
        {"marks_obtained": -1},
        {"marks_obtained": 101},
        {"passing_marks": 101},
        {"maximum_marks": 0},
        {"code": "X" * 31},
        {"grade_point": 10},
    ],
)
def test_validation(client, student_headers, patch):
    response = client.post(
        f"{ROOT}/1/subjects",
        headers=student_headers,
        json={**SUBJECT, **patch},
    )
    assert response.status_code == 422
    assert get_data(
        client, student_headers
    )["semesters"][0]["subjects"] == []


def test_duplicates_and_semester_bounds(
    client, student_headers
):
    add(client, student_headers)

    assert client.post(
        f"{ROOT}/1/subjects",
        headers=student_headers,
        json={**SUBJECT, "code": " ma101 "},
    ).status_code == 409

    add(client, student_headers, semester=2)

    assert client.post(
        f"{ROOT}/9/subjects",
        headers=student_headers,
        json=SUBJECT,
    ).status_code == 404


def test_incomplete_failed_and_policy(
    client, student_headers, admin_headers
):
    data = add(
        client, student_headers, marks_obtained=None
    )
    assert data["total"]["gpa"] is None

    data = add(
        client,
        student_headers,
        code="FAIL",
        credits=2,
        marks_obtained=39,
    )
    assert data["total"]["gpa"] == 0
    assert data["total"]["completed_credits"] == 0
    assert data["total"]["completed_semesters"] == 0

    configure(
        client,
        admin_headers,
        include_failed=False,
        conversion="(gpa - 0.75) * 10",
    )

    assert get_data(
        client, student_headers
    )["total"]["gpa"] is None

    data = add(
        client,
        student_headers,
        semester=2,
        credits=3,
        code="PASS",
    )

    assert data["total"]["gpa"] == 10
    assert (
        data["total"]["converted_percentage"]
        == 92.5
    )
    assert data["total"]["raw_percentage"] == 64.5

    configure(
        client, admin_headers, include_failed=True
    )
    assert get_data(
        client, student_headers
    )["total"]["gpa"] == 6

    summary = client.get(
        "/api/students/me/dashboard",
        headers=student_headers,
    ).get_json()["data"]
    assert summary["cgpa"] == 6


@pytest.mark.parametrize(
    "mark,grade,point",
    [
        (0, "F", 0),
        (39.99, "F", 0),
        (40, "P", 4),
        (45, "C", 5),
        (50, "B", 6),
        (60, "B+", 7),
        (70, "A", 8),
        (80, "A+", 9),
        (90, "O", 10),
        (100, "O", 10),
    ],
)
def test_grade_boundaries(
    client, student_headers, mark, grade, point
):
    subject = add(
        client,
        student_headers,
        marks_obtained=mark,
    )["semesters"][0]["subjects"][0]

    assert (
        subject["grade"], subject["grade_point"]
    ) == (grade, point)


def test_subject_minimum_overrides_band(
    client, student_headers
):
    subject = add(
        client,
        student_headers,
        passing_marks=95,
    )["semesters"][0]["subjects"][0]

    assert subject["result"] == "Fail"
    assert subject["grade"] == "F"


def test_policy_authorization_validation_and_recalculation(
    client, student_headers, admin_headers
):
    add(client, student_headers)

    current = client.get(
        f"{ROOT}/policy",
        headers=admin_headers,
    ).get_json()["data"]

    assert client.put(
        f"{ROOT}/policy",
        headers=student_headers,
        json=current,
    ).status_code == 403

    bad = deepcopy(current)
    bad["configuration"]["bands"][1]["min"] = 39

    assert client.put(
        f"{ROOT}/policy",
        headers=admin_headers,
        json=bad,
    ).status_code == 422

    for expression in (
        "__import__('os')",
        "1 / (gpa - 3)",
        "gpa * gpa",
    ):
        bad = deepcopy(current)
        bad["configuration"]["conversion"] = expression

        assert client.put(
            f"{ROOT}/policy",
            headers=admin_headers,
            json=bad,
        ).status_code == 422

    configuration = deepcopy(DEFAULT_POLICY)
    configuration["bands"][-1]["min"] = 95
    configuration["bands"][-2]["max"] = 95

    configure(
        client, admin_headers, **configuration
    )
    assert get_data(
        client, student_headers
    )["total"]["gpa"] == 9

    assert client.put(
        f"{ROOT}/policy",
        headers=admin_headers,
        json=current,
    ).status_code == 409

    assert convert(
        "(gpa - 0.75)*10", Decimal(9), 10
    ) == Decimal("82.50")


def test_absolute_marks_policy(
    client, student_headers, admin_headers
):
    configuration = deepcopy(DEFAULT_POLICY)
    configuration["basis"] = "marks"
    configuration["boundary_max"] = 200

    for band in configuration["bands"]:
        band["min"] *= 2
        band["max"] *= 2

    configure(
        client, admin_headers, **configuration
    )
    subject = add(
        client,
        student_headers,
        maximum_marks=200,
        passing_marks=80,
        marks_obtained=180,
    )["semesters"][0]["subjects"][0]

    assert subject["grade"] == "O"

    assert client.post(
        f"{ROOT}/2/subjects",
        headers=student_headers,
        json={**SUBJECT, "maximum_marks": 201},
    ).status_code == 422


def test_isolation_and_login_persistence(
    client,
    student_headers,
    other_headers,
    admin_headers,
):
    subject = add(
        client, student_headers
    )["semesters"][0]["subjects"][0]

    url = f"{ROOT}/1/subjects/{subject['id']}"

    assert client.put(
        url,
        headers=other_headers,
        json={**SUBJECT, "version": 1},
    ).status_code == 404

    assert client.delete(
        url,
        headers=other_headers,
        json={"version": 1},
    ).status_code == 404

    assert get_data(
        client, other_headers
    )["total"]["gpa"] is None

    assert client.get(ROOT).status_code == 401

    assert client.get(
        ROOT, headers=admin_headers
    ).status_code == 403

    assert client.post(
        "/api/auth/logout",
        headers=student_headers,
    ).status_code == 200

    assert client.get(
        ROOT, headers=student_headers
    ).status_code == 401

    headers = login_headers(
        client, "student@example.com"
    )
    assert get_data(
        client, headers
    )["total"]["gpa"] == 10

    assert get_data(
        client, other_headers
    )["student"]["name"] == "Other Student"


def test_legacy_preserved(
    client, student, student_headers
):
    scale = GradingScale(
        name="Historical",
        max_grade_point=10,
        is_template=True,
    )
    semester = Semester(
        user_id=student.id,
        number=3,
        grading_scale=scale,
    )
    old = Subject(
        name="Legacy",
        code="OLD",
        credits=4,
        grade_label="A",
        grade_point=8,
        counts_in_gpa=True,
    )
    semester.subjects.append(old)
    db.session.add(semester)
    db.session.commit()

    data = get_data(client, student_headers)
    saved = data["semesters"][2]["subjects"][0]

    assert saved["legacy_grade"] == "A"
    assert saved["maximum_marks"] is None
    assert data["total"]["gpa"] is None
    assert old.grade_point == 8


def test_pdf_and_excel_saved_records(
    client, student_headers, other_headers
):
    add(
        client,
        student_headers,
        name="=REAL_PRIVATE_SUBJECT",
    )

    response = client.get(
        f"{ROOT}/report.pdf",
        headers=student_headers,
    )
    assert response.status_code == 200
    assert response.data.startswith(b"%PDF")

    pdf = PdfReader(BytesIO(response.data))
    text = "\n".join(
        page.extract_text() for page in pdf.pages
    )

    for expected in [
        "REAL_PRIVATE_SUBJECT",
        "Test Student",
        "TOTAL CGPA",
        "90",
        "10.0",
        "Page 1 of",
    ] + [
        f"Semester {number}"
        for number in range(1, 9)
    ]:
        assert expected in text

    other = PdfReader(
        BytesIO(
            client.get(
                f"{ROOT}/report.pdf",
                headers=other_headers,
            ).data
        )
    )
    assert "REAL_PRIVATE_SUBJECT" not in "".join(
        page.extract_text()
        for page in other.pages
    )

    response = client.get(
        f"{ROOT}/report.xlsx",
        headers=student_headers,
    )
    workbook = load_workbook(
        BytesIO(response.data)
    )

    assert len(workbook.sheetnames) == 9
    assert (
        workbook["Semester 1"]["A2"].value
        == "'=REAL_PRIVATE_SUBJECT"
    )
    assert (
        workbook["Semester 1"]["A2"].data_type
        == "s"
    )
    assert (
        workbook["Semester 1"]["E2"].value
        == 90
    )
