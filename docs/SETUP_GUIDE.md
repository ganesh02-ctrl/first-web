# Local setup guide (Windows 11 / PowerShell)

## Prerequisites

- Python 3.11 or newer
- Node.js 20 or newer and npm
- MySQL 8.0 (or Docker Desktop with Docker Compose)
- Git is optional

## 1. Configure environment

From the project root:

```powershell
Copy-Item .env.example .env
```

Edit `.env`. Set `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DATABASE`, `MYSQL_USER`, and `MYSQL_PASSWORD` for your MySQL instance. Set non-empty `SECRET_KEY` and `JWT_SECRET_KEY` values for development. For production, use random secrets of at least 32 characters and set `APP_ENV=production`.

The frontend uses `VITE_API_BASE_URL=http://localhost:5000/api` by default. If you change the backend address, update this value before building the frontend.

## 2. Create the database

Create a MySQL database and user matching `.env`, or use the included Docker Compose database service. For a local MySQL installation, run a command similar to this in MySQL Workbench or the MySQL shell (replace the password):

```sql
CREATE DATABASE sss_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'sss_user'@'localhost' IDENTIFIED BY 'replace-with-a-strong-password';
GRANT ALL PRIVILEGES ON sss_db.* TO 'sss_user'@'localhost';
FLUSH PRIVILEGES;
```

## 3. Install and migrate the backend

```powershell
cd backend
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
flask --app run.py db upgrade
```

If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal and activate again.

Create the first admin:

```powershell
flask --app run.py create-admin --email admin@example.com --password "Use-A-Strong-Password-Here" --name "Administrator"
```

Run the backend:

```powershell
python run.py
```

API base: `http://localhost:5000/api`. Health endpoint: `http://localhost:5000/api/health`.

## 4. Install and run the frontend

Open a second PowerShell terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL printed in the terminal (normally `http://localhost:5173`).

## 5. Optional email and SMS

Email requires valid SMTP settings (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `MAIL_FROM`). SMS requires a supported provider and its credentials. Leave these unset until you have real credentials. The app should not claim a delivery was sent when a provider is not configured.

## 6. Tests and build checks

Backend (from `backend/`, with the virtual environment active):

```powershell
python -m compileall app tests
pytest -q
```

Frontend (from `frontend/`):

```powershell
npm test
npm run build
```

These commands are provided as checks; this source package has not yet had all of them successfully executed. Fix any reported errors before using the app.

## 7. Docker option

The included `docker-compose.yml` maps MySQL to host port `3307`, backend to `5000`, and frontend to `8080`. After editing `.env` with database credentials and secrets, from the project root run:

```powershell
docker compose up --build
```

This requires Docker Desktop. Review the compose configuration and secrets before any public deployment.

## 8. Real scholarship data

The initial database intentionally contains no scholarship records. An admin can create records in the admin interface or import a CSV. Imported rows remain unverified and unpublished until an administrator checks the official source and verifies them. Read `DATA_SOURCING_POLICY.md` first. Do not use example/test records as real scholarships.
