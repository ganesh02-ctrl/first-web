"""Initial SSS schema (all tables, including users.password_changed_at).

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-11-03
"""
import sqlalchemy as sa
from alembic import op

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None

# Frozen enum values (do not import app constants into migrations).
ROLES = ("student", "admin")
PROVIDER_TYPES = ("central_government", "state_government", "university", "institution", "private", "other")
SCHOLARSHIP_TYPES = ("merit", "need_based", "merit_cum_means", "minority", "disability", "sports",
                     "research", "girl_students", "other")
VERIFICATION = ("unverified", "verified", "needs_review", "expired")
CRITERIA = ("education_level", "income", "category", "gender", "state", "academic", "domicile", "age", "other")
APP_STATUSES = ("interested", "preparing_documents", "ready_to_apply", "applied", "approved", "rejected")
KINDS = ("deadline_reminder", "application_update", "system", "account")
CHANNELS = ("in_app", "email", "sms")
DELIVERY = ("pending", "sent", "failed", "skipped")
ACH_CATEGORIES = ("academic", "technical", "sports", "cultural", "leadership", "certifications", "other")
REPORT_REASONS = ("wrong_deadline", "broken_link", "wrong_eligibility", "wrong_amount", "expired", "other")
REPORT_STATUSES = ("open", "reviewing", "resolved", "dismissed")


def _id():
    return sa.Column("id", sa.Integer(), nullable=False)


def _ts():
    return [sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False)]


def _pk(table):
    return sa.PrimaryKeyConstraint("id", name=f"pk_{table}")


def _fk(table, col, ref, ondelete):
    return sa.ForeignKeyConstraint([col], [f"{ref}.id"], name=f"fk_{table}_{col}_{ref}", ondelete=ondelete)


def _ix(table, *cols, unique=False, name=None):
    op.create_index(name or f"ix_{table}_{cols[0]}", table, list(cols), unique=unique)


def upgrade():
    op.create_table(
        "users", _id(),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.Enum(*ROLES, name="user_role"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("email_verified_at", sa.DateTime(), nullable=True),
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
        sa.Column("failed_login_count", sa.Integer(), nullable=False),
        sa.Column("locked_until", sa.DateTime(), nullable=True),
        sa.Column("password_changed_at", sa.DateTime(), nullable=True),
        *_ts(), _pk("users"))
    _ix("users", "email", unique=True)
    _ix("users", "role")

    op.create_table(
        "scholarship_categories", _id(),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        *_ts(), _pk("scholarship_categories"),
        sa.UniqueConstraint("name", name="uq_scholarship_categories_name"),
        sa.UniqueConstraint("slug", name="uq_scholarship_categories_slug"))

    op.create_table(
        "student_profiles", _id(),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(150), nullable=False),
        sa.Column("phone", sa.String(20)), sa.Column("date_of_birth", sa.Date()),
        sa.Column("gender", sa.String(30)), sa.Column("state", sa.String(80)),
        sa.Column("district", sa.String(80)), sa.Column("college", sa.String(200)),
        sa.Column("university", sa.String(200)), sa.Column("degree", sa.String(120)),
        sa.Column("branch", sa.String(120)), sa.Column("education_level", sa.String(30)),
        sa.Column("current_semester", sa.SmallInteger()), sa.Column("graduation_year", sa.SmallInteger()),
        sa.Column("social_category", sa.String(30)), sa.Column("annual_family_income", sa.Numeric(12, 2)),
        sa.Column("academic_summary", sa.Text()), sa.Column("preferred_scholarship_types", sa.JSON()),
        sa.Column("preferred_states", sa.JSON()),
        sa.Column("public_portfolio_enabled", sa.Boolean(), nullable=False),
        sa.Column("public_slug", sa.String(32)),
        *_ts(), _pk("student_profiles"), _fk("student_profiles", "user_id", "users", "CASCADE"),
        sa.UniqueConstraint("user_id", name="uq_student_profiles_user_id"),
        sa.UniqueConstraint("public_slug", name="uq_student_profiles_public_slug"))
    _ix("student_profiles", "state")

    op.create_table(
        "notification_preferences", _id(),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("in_app_enabled", sa.Boolean(), nullable=False),
        sa.Column("email_enabled", sa.Boolean(), nullable=False),
        sa.Column("sms_enabled", sa.Boolean(), nullable=False),
        sa.Column("deadline_reminders", sa.Boolean(), nullable=False),
        sa.Column("application_updates", sa.Boolean(), nullable=False),
        sa.Column("reminder_days", sa.JSON(), nullable=False),
        *_ts(), _pk("notification_preferences"),
        _fk("notification_preferences", "user_id", "users", "CASCADE"),
        sa.UniqueConstraint("user_id", name="uq_notification_preferences_user_id"))

    op.create_table(
        "scholarships", _id(),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(280), nullable=False),
        sa.Column("provider_name", sa.String(255), nullable=False),
        sa.Column("provider_type", sa.Enum(*PROVIDER_TYPES, name="provider_type"), nullable=False),
        sa.Column("scholarship_type", sa.Enum(*SCHOLARSHIP_TYPES, name="scholarship_type"), nullable=False),
        sa.Column("category_id", sa.Integer()),
        sa.Column("state", sa.String(80)), sa.Column("academic_year", sa.String(20)),
        sa.Column("description", sa.Text()), sa.Column("benefits", sa.Text()),
        sa.Column("amount_text", sa.String(255)), sa.Column("amount_max", sa.Numeric(12, 2)),
        sa.Column("application_open_date", sa.Date()), sa.Column("application_close_date", sa.Date()),
        sa.Column("official_source_name", sa.String(255), nullable=False),
        sa.Column("source_url", sa.String(1000), nullable=False),
        sa.Column("application_url", sa.String(1000), nullable=False),
        sa.Column("verification_status", sa.Enum(*VERIFICATION, name="verification_status"), nullable=False),
        sa.Column("last_verified_at", sa.DateTime()),
        sa.Column("verified_by_id", sa.Integer()),
        sa.Column("verification_notes", sa.Text()),
        sa.Column("is_published", sa.Boolean(), nullable=False),
        sa.Column("created_by_id", sa.Integer()),
        *_ts(), _pk("scholarships"),
        _fk("scholarships", "category_id", "scholarship_categories", "SET NULL"),
        _fk("scholarships", "verified_by_id", "users", "SET NULL"),
        _fk("scholarships", "created_by_id", "users", "SET NULL"),
        sa.UniqueConstraint("slug", name="uq_scholarships_slug"))
    for col in ("title", "scholarship_type", "category_id", "state", "application_close_date", "verification_status"):
        _ix("scholarships", col)
    _ix("scholarships", "is_published", "application_close_date", name="ix_scholarships_publish_deadline")

    op.create_table(
        "scholarship_eligibility", _id(),
        sa.Column("scholarship_id", sa.Integer(), nullable=False),
        sa.Column("criterion_type", sa.Enum(*CRITERIA, name="eligibility_criterion"), nullable=False),
        sa.Column("value", sa.String(120)), sa.Column("numeric_value", sa.Numeric(12, 2)),
        sa.Column("description", sa.String(1000), nullable=False),
        _pk("scholarship_eligibility"),
        _fk("scholarship_eligibility", "scholarship_id", "scholarships", "CASCADE"))
    _ix("scholarship_eligibility", "scholarship_id")
    _ix("scholarship_eligibility", "criterion_type", "value", name="ix_eligibility_type_value")

    op.create_table(
        "scholarship_documents", _id(),
        sa.Column("scholarship_id", sa.Integer(), nullable=False),
        sa.Column("document_type", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("is_mandatory", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.String(500)),
        _pk("scholarship_documents"),
        _fk("scholarship_documents", "scholarship_id", "scholarships", "CASCADE"))
    _ix("scholarship_documents", "scholarship_id")

    op.create_table(
        "tracked_scholarships", _id(),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("scholarship_id", sa.Integer(), nullable=False),
        sa.Column("is_bookmarked", sa.Boolean(), nullable=False),
        sa.Column("reminders_enabled", sa.Boolean(), nullable=False),
        *_ts(), _pk("tracked_scholarships"),
        _fk("tracked_scholarships", "user_id", "users", "CASCADE"),
        _fk("tracked_scholarships", "scholarship_id", "scholarships", "CASCADE"),
        sa.UniqueConstraint("user_id", "scholarship_id", name="uq_tracked_user_scholarship"))
    _ix("tracked_scholarships", "user_id")
    _ix("tracked_scholarships", "scholarship_id")

    op.create_table(
        "scholarship_applications", _id(),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("scholarship_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.Enum(*APP_STATUSES, name="application_status"), nullable=False),
        sa.Column("applied_on", sa.Date()), sa.Column("application_reference", sa.String(120)),
        sa.Column("notes", sa.Text()),
        *_ts(), _pk("scholarship_applications"),
        _fk("scholarship_applications", "user_id", "users", "CASCADE"),
        _fk("scholarship_applications", "scholarship_id", "scholarships", "CASCADE"),
        sa.UniqueConstraint("user_id", "scholarship_id", name="uq_application_user_scholarship"))
    for col in ("user_id", "scholarship_id", "status"):
        _ix("scholarship_applications", col)

    op.create_table(
        "application_status_history", _id(),
        sa.Column("application_id", sa.Integer(), nullable=False),
        sa.Column("from_status", sa.String(30)), sa.Column("to_status", sa.String(30), nullable=False),
        sa.Column("note", sa.String(500)), sa.Column("changed_at", sa.DateTime(), nullable=False),
        _pk("application_status_history"),
        _fk("application_status_history", "application_id", "scholarship_applications", "CASCADE"))
    _ix("application_status_history", "application_id")

    op.create_table(
        "notifications", _id(),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("scholarship_id", sa.Integer()),
        sa.Column("kind", sa.Enum(*KINDS, name="notification_kind"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("link", sa.String(500)), sa.Column("reminder_days", sa.SmallInteger()),
        sa.Column("dedupe_key", sa.String(191)),
        sa.Column("is_read", sa.Boolean(), nullable=False), sa.Column("read_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        _pk("notifications"),
        _fk("notifications", "user_id", "users", "CASCADE"),
        _fk("notifications", "scholarship_id", "scholarships", "SET NULL"),
        sa.UniqueConstraint("dedupe_key", name="uq_notifications_dedupe_key"))
    _ix("notifications", "scholarship_id")
    _ix("notifications", "user_id", "is_read", "created_at", name="ix_notifications_user_read")

    op.create_table(
        "notification_deliveries", _id(),
        sa.Column("notification_id", sa.Integer(), nullable=False),
        sa.Column("channel", sa.Enum(*CHANNELS, name="delivery_channel"), nullable=False),
        sa.Column("status", sa.Enum(*DELIVERY, name="delivery_status"), nullable=False),
        sa.Column("recipient", sa.String(255)),
        sa.Column("attempts", sa.SmallInteger(), nullable=False),
        sa.Column("max_attempts", sa.SmallInteger(), nullable=False),
        sa.Column("last_error", sa.Text()), sa.Column("next_attempt_at", sa.DateTime()),
        sa.Column("sent_at", sa.DateTime()), sa.Column("provider_message_id", sa.String(255)),
        *_ts(), _pk("notification_deliveries"),
        _fk("notification_deliveries", "notification_id", "notifications", "CASCADE"),
        sa.UniqueConstraint("notification_id", "channel", name="uq_delivery_notification_channel"))
    _ix("notification_deliveries", "status", "next_attempt_at", name="ix_deliveries_status_next")

    op.create_table(
        "grading_scales", _id(),
        sa.Column("name", sa.String(150), nullable=False), sa.Column("description", sa.String(500)),
        sa.Column("max_grade_point", sa.Numeric(4, 2), nullable=False),
        sa.Column("owner_user_id", sa.Integer()),
        sa.Column("is_template", sa.Boolean(), nullable=False),
        *_ts(), _pk("grading_scales"), _fk("grading_scales", "owner_user_id", "users", "CASCADE"))
    _ix("grading_scales", "owner_user_id")

    op.create_table(
        "grade_mappings", _id(),
        sa.Column("scale_id", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(10), nullable=False),
        sa.Column("grade_point", sa.Numeric(4, 2), nullable=False),
        sa.Column("min_percent", sa.Numeric(5, 2)), sa.Column("max_percent", sa.Numeric(5, 2)),
        sa.Column("counts_in_gpa", sa.Boolean(), nullable=False),
        sa.Column("is_passing", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.SmallInteger(), nullable=False),
        _pk("grade_mappings"), _fk("grade_mappings", "scale_id", "grading_scales", "CASCADE"),
        sa.UniqueConstraint("scale_id", "label", name="uq_grade_scale_label"))

    op.create_table(
        "semesters", _id(),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("grading_scale_id", sa.Integer()),
        sa.Column("number", sa.SmallInteger(), nullable=False),
        sa.Column("title", sa.String(100)), sa.Column("academic_year", sa.String(20)),
        sa.Column("notes", sa.String(500)),
        *_ts(), _pk("semesters"),
        _fk("semesters", "user_id", "users", "CASCADE"),
        _fk("semesters", "grading_scale_id", "grading_scales", "SET NULL"),
        sa.UniqueConstraint("user_id", "number", name="uq_semester_user_number"))
    _ix("semesters", "user_id")

    op.create_table(
        "subjects", _id(),
        sa.Column("semester_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False), sa.Column("code", sa.String(30)),
        sa.Column("credits", sa.Numeric(5, 2), nullable=False),
        sa.Column("grade_label", sa.String(10), nullable=False),
        sa.Column("grade_point", sa.Numeric(4, 2), nullable=False),
        sa.Column("counts_in_gpa", sa.Boolean(), nullable=False),
        *_ts(), _pk("subjects"), _fk("subjects", "semester_id", "semesters", "CASCADE"))
    _ix("subjects", "semester_id")

    op.create_table(
        "document_folders", _id(),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        *_ts(), _pk("document_folders"), _fk("document_folders", "user_id", "users", "CASCADE"),
        sa.UniqueConstraint("user_id", "name", name="uq_folder_user_name"))
    _ix("document_folders", "user_id")

    op.create_table(
        "uploaded_documents", _id(),
        sa.Column("user_id", sa.Integer(), nullable=False), sa.Column("folder_id", sa.Integer()),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("stored_filename", sa.String(100), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("document_type", sa.String(50), nullable=False),
        sa.Column("issued_on", sa.Date()), sa.Column("expires_on", sa.Date()),
        *_ts(), _pk("uploaded_documents"),
        _fk("uploaded_documents", "user_id", "users", "CASCADE"),
        _fk("uploaded_documents", "folder_id", "document_folders", "SET NULL"),
        sa.UniqueConstraint("stored_filename", name="uq_uploaded_documents_stored_filename"))
    _ix("uploaded_documents", "folder_id")
    _ix("uploaded_documents", "expires_on")
    _ix("uploaded_documents", "user_id", "document_type", name="ix_documents_user_type")

    op.create_table(
        "achievements", _id(),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False), sa.Column("description", sa.Text()),
        sa.Column("organization", sa.String(200)),
        sa.Column("category", sa.Enum(*ACH_CATEGORIES, name="achievement_category"), nullable=False),
        sa.Column("achieved_on", sa.Date(), nullable=False),
        sa.Column("rank_position", sa.String(100)), sa.Column("location_name", sa.String(255)),
        sa.Column("latitude", sa.Numeric(9, 6)), sa.Column("longitude", sa.Numeric(9, 6)),
        sa.Column("certificate_document_id", sa.Integer()),
        sa.Column("is_public", sa.Boolean(), nullable=False),
        *_ts(), _pk("achievements"),
        _fk("achievements", "user_id", "users", "CASCADE"),
        _fk("achievements", "certificate_document_id", "uploaded_documents", "SET NULL"))
    _ix("achievements", "category")
    _ix("achievements", "user_id", "achieved_on", name="ix_achievements_user_date")

    op.create_table(
        "admin_logs", _id(),
        sa.Column("admin_id", sa.Integer()), sa.Column("action", sa.String(80), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False), sa.Column("entity_id", sa.Integer()),
        sa.Column("details", sa.JSON()), sa.Column("ip_address", sa.String(45)),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        _pk("admin_logs"), _fk("admin_logs", "admin_id", "users", "SET NULL"))
    for col in ("admin_id", "action", "created_at"):
        _ix("admin_logs", col)
    _ix("admin_logs", "entity_type", "entity_id", name="ix_admin_logs_entity")

    op.create_table(
        "scholarship_reports", _id(),
        sa.Column("scholarship_id", sa.Integer(), nullable=False), sa.Column("reporter_id", sa.Integer()),
        sa.Column("reason", sa.Enum(*REPORT_REASONS, name="report_reason"), nullable=False),
        sa.Column("details", sa.Text(), nullable=False),
        sa.Column("status", sa.Enum(*REPORT_STATUSES, name="report_status"), nullable=False),
        sa.Column("admin_notes", sa.Text()), sa.Column("resolved_by_id", sa.Integer()),
        sa.Column("resolved_at", sa.DateTime()),
        *_ts(), _pk("scholarship_reports"),
        _fk("scholarship_reports", "scholarship_id", "scholarships", "CASCADE"),
        _fk("scholarship_reports", "reporter_id", "users", "SET NULL"),
        _fk("scholarship_reports", "resolved_by_id", "users", "SET NULL"))
    _ix("scholarship_reports", "scholarship_id")
    _ix("scholarship_reports", "status")

    for table in ("password_reset_tokens", "email_verification_tokens"):
        op.create_table(
            table, _id(),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("token_hash", sa.String(64), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False), sa.Column("used_at", sa.DateTime()),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            _pk(table), _fk(table, "user_id", "users", "CASCADE"),
            sa.UniqueConstraint("token_hash", name=f"uq_{table}_token_hash"))
        _ix(table, "user_id")

    op.create_table(
        "token_blocklist", _id(),
        sa.Column("jti", sa.String(64), nullable=False),
        sa.Column("token_type", sa.String(10), nullable=False),
        sa.Column("user_id", sa.Integer()),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        _pk("token_blocklist"), _fk("token_blocklist", "user_id", "users", "CASCADE"),
        sa.UniqueConstraint("jti", name="uq_token_blocklist_jti"))
    _ix("token_blocklist", "user_id")
    _ix("token_blocklist", "expires_at")


def downgrade():
    for table in ("token_blocklist", "email_verification_tokens", "password_reset_tokens", "scholarship_reports",
                  "admin_logs", "achievements", "uploaded_documents", "document_folders", "subjects", "semesters",
                  "grade_mappings", "grading_scales", "notification_deliveries", "notifications",
                  "application_status_history", "scholarship_applications", "tracked_scholarships",
                  "scholarship_documents", "scholarship_eligibility", "scholarships", "notification_preferences",
                  "student_profiles", "scholarship_categories", "users"):
        op.drop_table(table)
