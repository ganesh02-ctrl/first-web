SCALE = {"name": "My Test Scale", "max_grade_point": 10,
         "grades": [{"label": "A", "grade_point": 10}, {"label": "B", "grade_point": 8},
                    {"label": "P", "grade_point": 0, "counts_in_gpa": False}]}


def test_semester_subject_flow(client, student_headers):
    scale = client.post("/api/academics/scales", headers=student_headers, json=SCALE).get_json()["data"]
    sem = client.post("/api/academics/semesters", headers=student_headers,
                      json={"number": 1, "grading_scale_id": scale["id"]}).get_json()["data"]
    url = f"/api/academics/semesters/{sem['id']}/subjects"
    client.post(url, headers=student_headers, json={"name": "Maths", "credits": 4, "grade_label": "a"})
    r = client.post(url, headers=student_headers, json={"name": "Lab", "credits": 2, "grade_label": "B"})
    assert r.get_json()["data"]["sgpa"] == 9.33
    bad = client.post(url, headers=student_headers, json={"name": "X", "credits": 2, "grade_label": "Z"})
    assert bad.status_code == 400
    assert client.get("/api/academics/summary", headers=student_headers).get_json()["data"]["cgpa"] == 9.33
    pdf = client.get("/api/academics/report.pdf", headers=student_headers)
    assert pdf.status_code == 200 and pdf.data[:4] == b"%PDF"


def test_scale_edit_reuses_labels(client, student_headers):
    scale = client.post("/api/academics/scales", headers=student_headers, json=SCALE).get_json()["data"]
    r = client.put(f"/api/academics/scales/{scale['id']}", headers=student_headers, json=SCALE)
    assert r.status_code == 200


def test_cannot_see_other_users_semester(client, student_headers, other_headers):
    scale = client.post("/api/academics/scales", headers=student_headers, json=SCALE).get_json()["data"]
    sem = client.post("/api/academics/semesters", headers=student_headers,
                      json={"number": 1, "grading_scale_id": scale["id"]}).get_json()["data"]
    assert client.get(f"/api/academics/semesters/{sem['id']}", headers=other_headers).status_code == 404
