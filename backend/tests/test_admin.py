import io

PAYLOAD = {"title": "Admin Test Record", "provider_name": "Fixture", "provider_type": "other",
           "scholarship_type": "merit", "official_source_name": "Fixture source",
           "source_url": "https://example.org/s", "application_url": "https://example.org/a",
           "eligibility": [{"criterion_type": "other", "description": "Fixture rule"}]}


def test_create_verify_publish_flow(client, admin_headers):
    r = client.post("/api/admin/scholarships", headers=admin_headers, json=PAYLOAD)
    sid = r.get_json()["data"]["id"]
    assert r.get_json()["data"]["verification_status"] == "unverified"
    assert client.patch(f"/api/admin/scholarships/{sid}", headers=admin_headers,
                        json={"is_published": True}).status_code == 400
    client.post(f"/api/admin/scholarships/{sid}/verify", headers=admin_headers,
                json={"verification_status": "verified"})
    assert client.patch(f"/api/admin/scholarships/{sid}", headers=admin_headers,
                        json={"is_published": True}).status_code == 200
    logs = client.get("/api/admin/logs", headers=admin_headers).get_json()["data"]
    assert any(l["action"] == "scholarship.verify" for l in logs)


def test_bad_url_rejected(client, admin_headers):
    r = client.post("/api/admin/scholarships", headers=admin_headers, json={**PAYLOAD, "source_url": "javascript:x"})
    assert r.status_code == 422


def test_csv_import_is_unverified(client, admin_headers):
    csv = ("title,provider_name,provider_type,scholarship_type,official_source_name,source_url,application_url\n"
           "CSV Row,Fixture,other,merit,Src,https://example.org/s,https://example.org/a\n"
           "Bad Row,Fixture,not_a_type,merit,Src,https://example.org/s,https://example.org/a\n")
    r = client.post("/api/admin/scholarships/import", headers=admin_headers,
                    data={"file": (io.BytesIO(csv.encode()), "s.csv")}, content_type="multipart/form-data")
    body = r.get_json()["data"]
    assert body["created"] == 1 and len(body["errors"]) == 1
    rows = client.get("/api/admin/scholarships", headers=admin_headers).get_json()["data"]
    assert rows[0]["verification_status"] == "unverified" and not rows[0]["is_published"]


def test_admin_cannot_disable_self(client, admin, admin_headers):
    r = client.patch(f"/api/admin/users/{admin.id}", headers=admin_headers, json={"is_active": False})
    assert r.status_code == 400
