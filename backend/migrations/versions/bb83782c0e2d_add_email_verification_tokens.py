"""Compatibility bridge for the supplied duplicate baseline revision.

The original upgrade recreated 15 tables already created, with identical
columns, by 0001_initial_schema. Do not recreate or drop those tables.
Already-stamped databases do not execute this revision again.
"""
from alembic import op
import sqlalchemy as sa

revision = "bb83782c0e2d"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None

REQUIRED = {
    "achievements": (
        "id user_id title description organization category "
        "achieved_on rank_position location_name latitude longitude "
        "certificate_document_id is_public created_at updated_at"
    ),
    "admin_logs": (
        "id admin_id action entity_type entity_id details "
        "ip_address created_at"
    ),
    "application_status_history": (
        "id application_id from_status to_status note changed_at"
    ),
    "document_folders": (
        "id user_id name created_at updated_at"
    ),
    "email_verification_tokens": (
        "id user_id token_hash expires_at used_at created_at"
    ),
    "grade_mappings": (
        "id scale_id label grade_point min_percent max_percent "
        "counts_in_gpa is_passing sort_order"
    ),
    "grading_scales": (
        "id name description max_grade_point owner_user_id "
        "is_template created_at updated_at"
    ),
    "notification_deliveries": (
        "id notification_id channel status recipient attempts "
        "max_attempts last_error next_attempt_at sent_at "
        "provider_message_id created_at updated_at"
    ),
    "notifications": (
        "id user_id scholarship_id kind title message link "
        "reminder_days dedupe_key is_read read_at created_at"
    ),
    "password_reset_tokens": (
        "id user_id token_hash expires_at used_at created_at"
    ),
    "scholarship_reports": (
        "id scholarship_id reporter_id reason details status "
        "admin_notes resolved_by_id resolved_at created_at updated_at"
    ),
    "semesters": (
        "id user_id grading_scale_id number title academic_year "
        "notes created_at updated_at"
    ),
    "subjects": (
        "id semester_id name code credits grade_label grade_point "
        "counts_in_gpa created_at updated_at"
    ),
    "token_blocklist": (
        "id jti token_type user_id expires_at created_at"
    ),
    "uploaded_documents": (
        "id user_id folder_id display_name original_filename "
        "stored_filename mime_type size_bytes sha256 document_type "
        "issued_on expires_on created_at updated_at"
    ),
}


def upgrade():
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())

    for table, columns in REQUIRED.items():
        if table not in tables:
            raise RuntimeError(
                f"Baseline table missing: {table}. "
                "Restore or reconcile the existing schema; "
                "do not reset it."
            )

        actual = {
            column["name"]
            for column in inspector.get_columns(table)
        }
        missing = set(columns.split()) - actual

        if missing:
            raise RuntimeError(
                f"Baseline columns missing from {table}: "
                f"{sorted(missing)}"
            )


def downgrade():
    # This bridge never owned tables.
    # Downgrading must never delete baseline data.
    pass
