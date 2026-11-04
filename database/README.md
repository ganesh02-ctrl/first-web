# Database

The Alembic migration in `backend/migrations/versions/` is the **source of truth**. Create the schema with:

```powershell
cd backend
flask --app run.py db upgrade
```

`schema.sql` is a reference copy of the same DDL. Regenerate it after every schema change. Offline mode doesn't connect to a database; it only needs the MySQL dialect:

```powershell
cd backend
flask --app run.py db upgrade --sql > ..\database\schema.sql
```

The database ships with **no scholarship data**. Admins add records from official sources by hand or through a CSV import (see `docs/DATA_SOURCING_POLICY.md`).
