"""Test fixtures. Uses in-memory SQLite. All scholarship rows here are TEST FIXTURES (example.org), not real data."""
import itertools
import shutil
from datetime import timedelta

import pytest
from sqlalchemy import event

from app import create_app
from app.extensions import db as _db
from app.models import (NotificationPreference, Scholarship, ScholarshipDocument, ScholarshipEligibility,
                        StudentProfile, User)
from app.utils.timeutils import today_local, utcnow

PASSWORD = "Passw0rdOK"
_counter = itertools.count(1)


@pytest.fixture()
def app():
    app = create_app("testing")
    with app.app_context():
        engine = _db.engine

        # pysqlite needs this so SAVEPOINT (session.begin_nested) works correctly.
        @event.listens_for(engine, "connect")
        def _connect(dbapi_conn, _record):
            dbapi_conn.isolation_level = None

        @event.listens_for(engine, "begin")
        def _begin(conn):
            conn.exec_driver_sql("BEGIN")

        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()
        engine.dispose()
    shutil.rmtree(app.config["UPLOAD_FOLDER"], ignore_errors=True)


@pytest.fixture()
def client(app):
    return app.test_client()


def _make_user(email, role="student", name="Test Student", password=PASSWORD):
    user = User(email=email, role=role)
    user.set_password(password)
    user.profile = StudentProfile(full_name=name)
    user.notification_preference = NotificationPreference()
    _db.session.add(user)
    _db.session.commit()
    return user


def login_headers(client, email, password=PASSWORD):
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.get_json()
    return {"Authorization": f"Bearer {resp.get_json()['data']['access_token']}"}


@pytest.fixture()
def make_user(app):
    return _make_user


@pytest.fixture()
def student(app):
    return _make_user("student@example.com")


@pytest.fixture()
def student_headers(client, student):
    return login_headers(client, "student@example.com")


@pytest.fixture()
def other_headers(client, app):
    _make_user("other@example.com", name="Other Student")
    return login_headers(client, "other@example.com")


@pytest.fixture()
def admin(app):
    return _make_user("admin@example.com", role="admin", name="Admin")


@pytest.fixture()
def admin_headers(client, admin):
    return login_headers(client, "admin@example.com")


@pytest.fixture()
def make_scholarship(app):
    """Factory for TEST-ONLY scholarship rows. eligibility: list of (type, value, numeric_value)."""
    def factory(eligibility=(("education_level", "undergraduate", None),), documents=(), **overrides):
        n = next(_counter)
        values = dict(title=f"Test Fixture Scholarship {n}", slug=f"test-fixture-{n}",
                      provider_name="Fixture Provider", provider_type="other", scholarship_type="merit",
                      official_source_name="Test fixture (not real)", source_url="https://example.org/source",
                      application_url="https://example.org/apply", verification_status="verified",
                      last_verified_at=utcnow(), is_published=True,
                      application_close_date=today_local() + timedelta(days=30))
        values.update(overrides)
        sch = Scholarship(**values)
        sch.eligibility = [ScholarshipEligibility(criterion_type=t, value=v, numeric_value=nv, description=f"{t} rule")
                           for t, v, nv in eligibility]
        sch.required_documents = [ScholarshipDocument(document_type=d, name=d) for d in documents]
        _db.session.add(sch)
        _db.session.commit()
        return sch
    return factory
