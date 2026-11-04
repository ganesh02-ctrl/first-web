-- SSS database creation only; this is NOT the complete table DDL.
-- The authoritative table schema is backend/migrations/versions/0001_initial_schema.py.
-- From backend/ with the virtual environment active, apply it using:
--     flask --app run.py db upgrade
CREATE DATABASE IF NOT EXISTS sss_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
