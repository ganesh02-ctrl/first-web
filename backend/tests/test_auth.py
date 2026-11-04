from tests.conftest import PASSWORD, login_headers


def test_register_login_me_logout(client):
    r = client.post("/api/auth/register", json={"email": "New@Example.com", "password": PASSWORD,
                                                "full_name": "New Student"})
    assert r.status_code == 201
    headers = login_headers(client, "new@example.com")
    me = client.get("/api/auth/me", headers=headers)
    assert me.get_json()["data"]["user"]["email"] == "new@example.com"
    assert client.post("/api/auth/logout", headers=headers, json={}).status_code == 200
    assert client.get("/api/auth/me", headers=headers).status_code == 401


def test_weak_password_and_duplicate_rejected(client, student):
    r = client.post("/api/auth/register", json={"email": "x@example.com", "password": "short", "full_name": "Xx"})
    assert r.status_code == 422
    r = client.post("/api/auth/register", json={"email": "student@example.com", "password": PASSWORD,
                                                "full_name": "Dup"})
    assert r.status_code == 409


def test_wrong_password_and_lockout(client, student):
    for _ in range(5):
        assert client.post("/api/auth/login", json={"email": student.email, "password": "Wrong1234"}).status_code == 401
    r = client.post("/api/auth/login", json={"email": student.email, "password": PASSWORD})
    assert r.status_code == 403


def test_password_change_revokes_old_tokens(client, student_headers):
    import time
    time.sleep(1.1)  # JWT iat has 1-second resolution
    r = client.post("/api/auth/change-password", headers=student_headers,
                    json={"current_password": PASSWORD, "new_password": "NewPassw0rd"})
    assert r.status_code == 200
    assert client.get("/api/auth/me", headers=student_headers).status_code == 401


def test_forgot_password_no_enumeration(client):
    r = client.post("/api/auth/forgot-password", json={"email": "nobody@example.com"})
    assert r.status_code == 200


def test_protected_and_admin_routes(client, student_headers):
    assert client.get("/api/students/me/profile").status_code == 401
    assert client.get("/api/admin/dashboard", headers=student_headers).status_code == 403
