# API overview

Base URL: `http://localhost:5000/api`. JSON endpoints use the standard response envelope implemented in `backend/app/utils/responses.py`. Protected endpoints require `Authorization: Bearer <access_token>`.

## Health and public endpoints

- `GET /health` — backend/database/provider configuration health
- `GET /public/meta` — dropdown vocabularies
- `GET /public/portfolio/<slug>` — public achievement portfolio
- `GET /scholarships` — published scholarship search and pagination
- `GET /scholarships/categories` — scholarship categories
- `GET /scholarships/<id_or_slug>` — public scholarship details

## Authentication

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `GET /auth/me`
- `POST /auth/verify-email`
- `POST /auth/resend-verification`
- `POST /auth/forgot-password`
- `POST /auth/reset-password`
- `POST /auth/change-password`

## Student endpoints

- `GET/PATCH /students/me/profile`
- `GET /students/me/dashboard`
- `GET/PUT/DELETE /tracking` and `/tracking/<scholarship_id>`
- `GET/PUT/DELETE /applications` and `/applications/<scholarship_id>`
- `GET/POST /academics/scales`; `PUT/DELETE /academics/scales/<id>`
- `GET/POST /academics/semesters`; `GET/PUT/DELETE /academics/semesters/<id>`
- `POST/PUT/DELETE /academics/semesters/<id>/subjects/<subject_id>` (POST omits subject id)
- `GET /academics/summary`; `POST /academics/calculate`; `GET /academics/report.pdf`
- `GET/POST /achievements`; `GET/PUT/DELETE /achievements/<id>`; `GET /achievements/portfolio.pdf`
- `GET/POST /documents`, `PATCH/DELETE /documents/<id>`, download/preview routes, folders, checklist and types
- `GET /notifications`, unread count, read actions and preferences
- `POST /scholarships/<id>/report`

## Administrator endpoints

All `/admin/*` endpoints require an authenticated administrator. They cover dashboard, users, scholarship CRUD and verification, CSV import, categories, user reports, notification delivery logs, audit logs and manual reminder/delivery jobs. See `backend/app/routes/admin.py` for exact request schemas and response fields.

## Notes

This is an endpoint index, not a complete OpenAPI specification. Use the Marshmallow schemas under `backend/app/schemas/` as the request-validation source of truth. Pagination and exact filters are implemented in route/service modules.
