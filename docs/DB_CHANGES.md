# DB Changes Guide

## Goal
Avoid silent breakage when schema or queries change.

## Common failure mode
A query selects a column that does not exist in the DB.

Example:

SELECT kind FROM products

when products.kind does not exist will cause:

sqlite3.OperationalError: no such column: kind

## Schema source of truth
The schema is defined in:

backend/schema.sql

Queries in the codebase must match schema.sql exactly.

## DB access architecture
Database connections are created in:

backend/db.py

using db_session().

SQL queries are implemented in:

backend/repo/*
backend/api/*
backend/logic/*

## Workflow for changing schema

1) Edit backend/schema.sql

2) Rebuild the database

Move the old DB aside:

mv db/Lager_live.db db/Lager_live_backup.db

Create a fresh DB:

pipenv run python backend/init_db.py

3) Reimport data

Run import scripts such as:

scripts/import_products.py

4) Verify

Test:
- API endpoints
- frontend views
- admin page
- stock queries

## What not to do

Do not add columns directly in a live DB without updating schema.sql.

Do not modify the SQLite database manually and commit it.

Do not scatter schema definitions across multiple files.

schema.sql must remain the single source of truth.

## Never commit a modified Lager_live.db

The repository should treat the DB as disposable.

The database should always be reproducible from:

backend/schema.sql
scripts/import_*.py