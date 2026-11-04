from datetime import timedelta

from app.utils.timeutils import today_local


def test_unpublished_and_expired_hidden(client, make_scholarship):
    make_scholarship(title="Visible One")
    make_scholarship(title="Hidden Draft", is_published=False)
    make_scholarship(title="Old One", application_close_date=today_local() - timedelta(days=1))
    titles = [s["title"] for s in client.get("/api/scholarships").get_json()["data"]]
    assert titles == ["Visible One"]


def test_filters(client, make_scholarship):
    make_scholarship(title="UG Low", eligibility=[("education_level", "undergraduate", None),
                                                   ("income", None, 100000)])
    make_scholarship(title="PG", eligibility=[("education_level", "postgraduate", None)], state="Karnataka")
    r = client.get("/api/scholarships?education_level=undergraduate").get_json()["data"]
    assert [s["title"] for s in r] == ["UG Low"]
    r = client.get("/api/scholarships?income=200000").get_json()["data"]
    assert [s["title"] for s in r] == ["PG"]
    r = client.get("/api/scholarships?state=Kerala").get_json()["data"]
    assert [s["title"] for s in r] == ["UG Low"]
    assert client.get("/api/scholarships?education_level=bogus").status_code == 422


def test_track_and_application_status(client, student_headers, make_scholarship):
    sch = make_scholarship()
    assert client.put(f"/api/tracking/{sch.id}", headers=student_headers, json={"is_bookmarked": True}).status_code == 200
    client.put(f"/api/applications/{sch.id}", headers=student_headers, json={"status": "interested"})
    r = client.put(f"/api/applications/{sch.id}", headers=student_headers, json={"status": "applied"})
    assert len(r.get_json()["data"]["history"]) == 2
    notes = client.get("/api/notifications", headers=student_headers).get_json()["data"]
    assert notes[0]["kind"] == "application_update"
