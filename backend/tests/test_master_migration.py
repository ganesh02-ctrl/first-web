"""File-backed SQLite migration and process-restart persistence checks."""
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

BACKEND = Path(__file__).resolve().parents[1]


def test_migration_preserves_historical_records_across_processes(
    tmp_path,
):
    path = tmp_path / "migration.sqlite"
    environment = {
        **os.environ,
        "APP_ENV": "testing",
        "TEST_DATABASE_URL": (
            "sqlite:///" + path.as_posix()
        ),
    }

    def migrate(revision):
        subprocess.run(
            [
                sys.executable,
                "-m",
                "flask",
                "--app",
                "run.py",
                "db",
                "upgrade",
                revision,
            ],
            cwd=BACKEND,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )

    migrate("bb83782c0e2d")

    with sqlite3.connect(path) as connection:
        connection.execute(
            "INSERT INTO users "
            "(id,email,password_hash,role,is_active,"
            "failed_login_count,created_at,updated_at) "
            "VALUES "
            "(1,'migration@example.com','test-only',"
            "'student',1,0,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)"
        )
        connection.execute(
            "INSERT INTO semesters "
            "(id,user_id,number,created_at,updated_at) "
            "VALUES "
            "(1,1,1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)"
        )
        connection.execute(
            "INSERT INTO subjects "
            "(id,semester_id,name,credits,grade_label,"
            "grade_point,counts_in_gpa,created_at,updated_at) "
            "VALUES "
            "(1,1,'Historical',4,'A',8,1,"
            "CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)"
        )

    migrate("head")

    with sqlite3.connect(path) as connection:
        row = connection.execute(
            "SELECT name,grade_label,grade_point,"
            "maximum_marks,master_managed,record_version "
            "FROM subjects WHERE id=1"
        ).fetchone()

        assert row == (
            "Historical",
            "A",
            8,
            None,
            0,
            1,
        )
        assert connection.execute(
            "SELECT version_num FROM alembic_version"
        ).fetchone()[0] == "msr_0001"

        assert connection.execute(
            "SELECT version FROM academic_policy"
        ).fetchone()[0] == 1

    # Save in a separate backend interpreter.
    program = (
        "from app import create_app; "
        "from app.extensions import db; "
        "from app.models import User; "
        "from app.services.master import save_subject; "
        "app=create_app('testing'); "
        "ctx=app.app_context(); ctx.push(); "
        "save_subject("
        "db.session.get(User,1),2,"
        "dict(name='Persisted',code='P2',credits=3,"
        "maximum_marks=100,passing_marks=40,marks_obtained=90)"
        ")"
    )
    subprocess.run(
        [sys.executable, "-c", program],
        cwd=BACKEND,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )

    # Read in another interpreter, representing a restarted backend.
    program = (
        "from app import create_app; "
        "from app.extensions import db; "
        "from app.models import User; "
        "from app.services.master import dashboard; "
        "app=create_app('testing'); "
        "ctx=app.app_context(); ctx.push(); "
        "assert dashboard("
        "db.session.get(User,1)"
        ")['total']['gpa']==10"
    )
    subprocess.run(
        [sys.executable, "-c", program],
        cwd=BACKEND,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )

    migrate("head")

    with sqlite3.connect(path) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM subjects"
        ).fetchone()[0] == 2
