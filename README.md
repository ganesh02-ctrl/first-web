# SSS — Student Support System

A student-support web application with scholarship discovery and tracking, academic SGPA/CGPA tools, achievement portfolio, document vault, notifications, and an administrator workspace.

## Important data and readiness notes

- The database starts with **zero scholarship records**. This is intentional: the app does not invent scholarships or scrape portals. Administrators must add/import records from official sources and verify them before publishing.
- Email and SMS delivery require real provider credentials in `.env`. Without them, delivery is not reported as sent.
- The code was assembled from generated source batches. Python syntax compilation was checked during packaging, but application integration, database migrations, backend tests, and frontend build have **not yet been verified** in this environment. Treat this as a development build, not production-ready software.

## Project structure

- `frontend/` — React + TypeScript + Vite client
- `backend/` — Flask REST API, SQLAlchemy models/services/routes, migrations and tests
- `database/` — schema reference and notes
- `docs/` — data sourcing and database notes; see `SETUP_GUIDE.md` for local setup
- `.env.example` — environment variables; copy to `.env` and replace development secrets

## Quick start

See [`docs/SETUP_GUIDE.md`](docs/SETUP_GUIDE.md). On Windows, use PowerShell and start MySQL 8 before starting the backend.

## Admin setup

After migrations, create the first administrator with the Flask CLI command documented in the setup guide. Do not expose admin credentials in source control.

## Data integrity

Review [`docs/DATA_SOURCING_POLICY.md`](docs/DATA_SOURCING_POLICY.md) before importing or publishing scholarship records.
