"""Flask CLI commands: flask --app run.py <command>"""
import json
import os
from datetime import date
from pathlib import Path

import click
from flask import Flask

from app.extensions import db


def register_commands(app: Flask) -> None:

    @app.cli.command("create-admin")
    @click.option("--email", default=lambda: os.getenv("ADMIN_EMAIL", ""))
    @click.option("--password", default=lambda: os.getenv("ADMIN_PASSWORD", ""))
    @click.option("--name", default="Administrator")
    def create_admin(email, password, name):
        """Create (or promote) an administrator account."""
        from app.models import NotificationPreference, StudentProfile, User
        from app.utils.security import password_policy_errors
        email = (email or click.prompt("Admin email")).strip().lower()
        password = password or click.prompt("Admin password", hide_input=True, confirmation_prompt=True)
        if problems := password_policy_errors(password):
            raise click.ClickException(" ".join(problems))
        user = User.query.filter_by(email=email).first()
        if user:
            user.role, user.is_active = "admin", True
            user.set_password(password)
            click.echo(f"Existing user {email} promoted to admin and password reset.")
        else:
            user = User(email=email, role="admin")
            user.set_password(password)
            user.profile = StudentProfile(full_name=name)
            user.notification_preference = NotificationPreference(email_enabled=False)
            db.session.add(user)
            click.echo(f"Admin {email} created.")
        from app.utils.timeutils import utcnow
        user.email_verified_at = user.email_verified_at or utcnow()
        db.session.commit()

    @app.cli.command("run-reminders")
    @click.option("--date", "on_date", default=None, help="Simulate a day (YYYY-MM-DD)")
    def run_reminders(on_date):
        """Run the deadline reminder job once."""
        from app.services.reminder import run_deadline_reminders
        click.echo(json.dumps(run_deadline_reminders(date.fromisoformat(on_date) if on_date else None)))

    @app.cli.command("process-deliveries")
    def process_deliveries():
        """Send pending email/SMS deliveries and retry failures that are due."""
        from app.services.notification import process_pending_deliveries
        click.echo(json.dumps(process_pending_deliveries()))

    @app.cli.command("import-scholarships")
    @click.argument("csv_path", type=click.Path(exists=True, dir_okay=False))
    @click.option("--admin-email", required=True)
    @click.option("--dry-run", is_flag=True)
    def import_scholarships(csv_path, admin_email, dry_run):
        """Import a CSV. Rows are created unverified and unpublished."""
        from app.models import User
        from app.services.scholarship_import import import_csv
        admin = User.query.filter_by(email=admin_email.lower(), role="admin").first()
        if not admin:
            raise click.ClickException("Admin user not found")
        click.echo(json.dumps(import_csv(admin, Path(csv_path).read_bytes(), dry_run=dry_run), indent=2))

    @app.cli.command("import-grading-scale")
    @click.argument("json_path", type=click.Path(exists=True, dir_okay=False))
    @click.option("--admin-email", required=True)
    def import_grading_scale(json_path, admin_email):
        """Create a shared grading-scale template from YOUR university's official scale (JSON)."""
        from app.models import User
        from app.schemas.academic import GradingScaleSchema
        from app.schemas.common import load
        from app.services.academic import save_scale
        admin = User.query.filter_by(email=admin_email.lower(), role="admin").first()
        if not admin:
            raise click.ClickException("Admin user not found")
        data = load(GradingScaleSchema(), json.loads(Path(json_path).read_text(encoding="utf-8")))
        data["as_template"] = True
        scale = save_scale(admin, data)
        click.echo(f"Grading scale '{scale.name}' created (id {scale.id}).")

    @app.cli.command("purge-tokens")
    def purge_tokens():
        """Delete expired blocklist / reset / verification tokens."""
        from app.services.auth import purge_expired_tokens
        click.echo(f"Removed {purge_expired_tokens()} expired tokens.")
