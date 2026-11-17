# SSS — Public Production Deployment Guide

This guide describes how to publish the **SSS — Student Support System** with a single public HTTPS URL, accessible 24/7 from any device even when your personal computer is turned off.

---

## Architecture Overview

- **Frontend**: React + TypeScript + Vite SPA, served via CDN or Nginx.
- **Backend**: Python 3.12 + Flask API with Waitress WSGI server.
- **Database**: Managed MySQL 8.0 with persistent storage and automatic migrations (`msr_0001`).
- **Data Persistence**: Backups stored in `database/backup_production.sql`. Uploaded files stored in persistent volume `/app/uploads`.

---

## Option 1: Railway (Recommended — Fastest 1-Dashboard Deployment)

Railway provides managed MySQL, Docker support, automated SSL/HTTPS domains, and continuous deployment from GitHub in one unified dashboard.

### Step 1: Push Code to GitHub
Open PowerShell in the project directory:
```powershell
git add .
git commit -m "feat: complete Master Semester Records and production deployment configuration"
git push origin main
```

### Step 2: Create Railway Project
1. Go to [railway.com](https://railway.com/) and sign up / log in with your GitHub account.
2. Click **+ New Project** -> **Deploy from GitHub repo**.
3. Select your repository: `Ganesh02-SH/first-web`.

### Step 3: Add Managed MySQL Database
1. In your Railway project canvas, click **+ Create** -> **Database** -> **Add MySQL**.
2. Railway creates a managed MySQL 8.0 instance.
3. Click on the MySQL card -> **Variables** tab to view your credentials (`MYSQLHOST`, `MYSQLPORT`, `MYSQLDATABASE`, `MYSQLUSER`, `MYSQLPASSWORD`).

### Step 4: Configure Backend Service
1. Click **+ Create** -> **GitHub Repo** -> select `first-web`.
2. Name the service: `sss-backend`.
3. In service **Settings**:
   - **Root Directory**: `backend`
   - **Start Command**: `flask --app run.py db upgrade && waitress-serve --host=0.0.0.0 --port=$PORT run:app`
   - **Healthcheck Path**: `/api/health`
4. Under **Variables**, add:
   ```env
   APP_ENV=production
   SECRET_KEY=Generate_A_Random_64_Character_Secret_String_Here!
   JWT_SECRET_KEY=Generate_A_Second_Random_64_Character_Secret_String!
   JWT_ACCESS_TOKEN_MINUTES=30
   JWT_REFRESH_TOKEN_DAYS=14
   BCRYPT_ROUNDS=12
   MYSQL_HOST=${{MySQL.MYSQLHOST}}
   MYSQL_PORT=${{MySQL.MYSQLPORT}}
   MYSQL_DATABASE=${{MySQL.MYSQLDATABASE}}
   MYSQL_USER=${{MySQL.MYSQLUSER}}
   MYSQL_PASSWORD=${{MySQL.MYSQLPASSWORD}}
   CORS_ORIGINS=https://*
   ```
5. Click **Generate Domain** under Settings -> Networking to get your public backend URL (e.g., `https://sss-backend.up.railway.app`).

### Step 5: Configure Frontend Service
1. Click **+ Create** -> **GitHub Repo** -> select `first-web`.
2. Name the service: `sss-frontend`.
3. In service **Settings**:
   - **Root Directory**: `frontend`
   - **Build Command**: `npm ci && npm run build`
4. Under **Variables**, set:
   ```env
   VITE_API_BASE_URL=https://sss-backend.up.railway.app/api
   ```
5. Click **Generate Domain** under Settings -> Networking.
6. Your public HTTPS website is live at your custom Railway URL (e.g. `https://sss.up.railway.app`)!

---

## Option 2: Render (Free Tier Blueprint)

Render allows 1-click deployment using the included `render.yaml` blueprint.

1. Sign up / log in to [render.com](https://render.com/) with GitHub.
2. Click **New +** -> **Blueprint**.
3. Connect your repository: `Ganesh02-SH/first-web`.
4. Render detects `render.yaml` and provisions:
   - MySQL / Database service
   - Backend web service (`sss-backend`)
   - Frontend static site (`sss-frontend`)
5. Click **Apply**. Render will automatically build, link environment variables, and provide public HTTPS URLs.

---

## Restoring Existing Database Records to Production

To import your existing student profiles, scholarships, and master semester policies into the cloud database:

Using the exported `database/backup_production.sql`:
```bash
mysql -h <CLOUD_MYSQL_HOST> -P <PORT> -u <USER> -p<PASSWORD> <DATABASE_NAME> < database/backup_production.sql
```

---

## Updating the Website in the Future

Once connected to your hosting provider, updating the website requires only one command:
```powershell
git add .
git commit -m "Update feature"
git push origin main
```
Your hosting platform will automatically build and deploy the changes with zero downtime.
