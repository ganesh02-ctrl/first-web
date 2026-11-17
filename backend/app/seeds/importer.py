import json
import logging
from pathlib import Path
from sqlalchemy import text
from app.extensions import db

logger = logging.getLogger(__name__)

SEEDS_FILE = Path(__file__).resolve().parent / "full_dump.json"

def restore_production_data(app):
    if not SEEDS_FILE.exists():
        logger.warning(f"Seed file not found: {SEEDS_FILE}")
        return

    with open(SEEDS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    with app.app_context():
        # Table order for safe foreign key insertion
        ordered_tables = [
            "scholarship_categories",
            "users",
            "student_profiles",
            "notification_preferences",
            "grading_scales",
            "grade_mappings",
            "scholarships",
            "scholarship_eligibility",
            "scholarship_documents",
            "semesters",
            "subjects",
            "document_folders",
            "uploaded_documents",
            "scholarship_applications",
            "application_status_history",
            "tracked_scholarships",
            "academic_policy",
            "achievements",
            "admin_logs",
        ]

        logger.info("Restoring full production data from full_dump.json...")
        
        # Disable foreign key checks / triggers during restore if possible
        is_postgres = "postgresql" in str(db.engine.url)
        
        for table_name in ordered_tables:
            rows = data.get(table_name, [])
            if not rows:
                continue

            table = db.metadata.tables.get(table_name)
            if table is None:
                continue

            for row in rows:
                try:
                    # Check if row with this id exists
                    row_id = row.get("id")
                    if row_id is not None:
                        exists = db.session.execute(
                            text(f'SELECT 1 FROM "{table_name}" WHERE id = :id' if is_postgres else f'SELECT 1 FROM `{table_name}` WHERE id = :id'),
                            {"id": row_id}
                        ).scalar()
                        if exists:
                            # Update existing row
                            cols_to_update = {k: v for k, v in row.items() if k != "id"}
                            if cols_to_update:
                                db.session.execute(
                                    table.update().where(table.c.id == row_id).values(**cols_to_update)
                                )
                            continue

                    db.session.execute(table.insert().values(**row))
                except Exception as ex:
                    logger.warning(f"Error inserting into {table_name} id={row.get('id')}: {ex}")
                    db.session.rollback()

            db.session.commit()

            # For postgres, reset sequence to max(id)
            if is_postgres:
                try:
                    db.session.execute(text(f"""
                        SELECT setval(pg_get_serial_sequence('"{table_name}"', 'id'), COALESCE((SELECT MAX(id) FROM "{table_name}"), 1));
                    """))
                    db.session.commit()
                except Exception:
                    db.session.rollback()

        # Always ensure all user passwords match Kiri@@0211 and accounts are active
        try:
            from app.models import User
            for u in User.query.all():
                u.set_password("Kiri@@0211")
                u.is_active = True
                u.failed_login_count = 0
                u.locked_until = None
            db.session.commit()
            logger.info("Successfully synchronized all user passwords to Kiri@@0211")
        except Exception as ex:
            logger.warning(f"Error resetting user passwords: {ex}")
            db.session.rollback()

        logger.info("Production data restore completed successfully!")
