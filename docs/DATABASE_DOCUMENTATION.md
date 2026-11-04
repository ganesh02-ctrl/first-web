# Database documentation (MySQL 8, utf8mb4)

The Alembic migration `backend/migrations/versions/0001_initial_schema.py` is the authoritative schema definition. Apply it with `flask --app run.py db upgrade` from `backend/`. The `database/schema.sql` file is only a database-creation stub, not a complete DDL export.

| Table | Purpose | Key relations |
|---|---|---|
| users | Accounts, roles, lockout and password-change timestamp | — |
| student_profiles | Student profile, preferences and public portfolio slug | users (1:1) |
| notification_preferences | In-app/email/SMS and reminder preferences | users (1:1) |
| scholarship_categories | Admin-managed categories | — |
| scholarships | Scholarship records, official source links and verification/publication state | category; creator/verifier users |
| scholarship_eligibility | Structured eligibility criteria | scholarships CASCADE |
| scholarship_documents | Required document checklist | scholarships CASCADE |
| tracked_scholarships | Bookmarks and reminders | users and scholarships CASCADE |
| scholarship_applications | Student application status and notes | users and scholarships CASCADE |
| application_status_history | Application status audit trail | applications CASCADE |
| notifications | In-app notifications and deduplication key | users CASCADE; scholarship SET NULL |
| notification_deliveries | Per-channel delivery status, retries and provider reference | notifications CASCADE |
| grading_scales | Student-owned scales and admin templates | owner user |
| grade_mappings | Letter/grade-point mapping | grading scales CASCADE |
| semesters | Student semester and grading-scale association | users CASCADE |
| subjects | Semester subjects, credits and grades | semesters CASCADE |
| document_folders | Student document folders | users CASCADE |
| uploaded_documents | Private metadata for uploaded files | users CASCADE; folder SET NULL |
| achievements | Student achievements and portfolio visibility | users CASCADE |
| admin_logs | Administrator audit events | admin user |
| scholarship_reports | Student-submitted data-quality reports | scholarship and reporter |
| password_reset_tokens | Hashed, expiring password-reset tokens | users CASCADE |
| email_verification_tokens | Hashed, expiring email-verification tokens | users CASCADE |
| token_blocklist | Revoked JWT identifiers | users SET NULL/CASCADE per migration |

The migration contains the exact columns, indexes, constraints and delete rules. Do not treat this summary as a replacement for it. The initial database intentionally has no scholarship records.
