from datetime import timedelta

from app.models import Notification
from app.services.reminder import run_deadline_reminders
from app.utils.timeutils import today_local


def test_reminder_days_and_dedupe(app, client, student, student_headers, make_scholarship):
    sch = make_scholarship(application_close_date=today_local() + timedelta(days=7))
    client.put(f"/api/tracking/{sch.id}", headers=student_headers, json={})
    first = run_deadline_reminders()
    second = run_deadline_reminders()
    assert first["created"] == 1 and second["created"] == 0 and second["duplicates"] == 1
    note = Notification.query.filter_by(user_id=student.id).one()
    email = [d for d in note.deliveries if d.channel == "email"][0]
    assert email.status == "skipped"  # no SMTP configured: never reported as sent


def test_no_reminder_off_schedule_or_after_applying(app, client, student_headers, make_scholarship):
    a = make_scholarship(application_close_date=today_local() + timedelta(days=8))
    b = make_scholarship(application_close_date=today_local() + timedelta(days=3))
    for s in (a, b):
        client.put(f"/api/tracking/{s.id}", headers=student_headers, json={})
    client.put(f"/api/applications/{b.id}", headers=student_headers, json={"status": "applied"})
    assert run_deadline_reminders()["created"] == 0


def test_expired_marked(app, make_scholarship):
    sch = make_scholarship(application_close_date=today_local() - timedelta(days=2))
    run_deadline_reminders()
    assert sch.verification_status == "expired"
