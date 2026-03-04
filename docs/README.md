# Lager Projekt Documentation

## 1. Purpose
This project tracks workers and products in an SQLite database and serves data to the frontend.
The main reliability risks are schema drift and ad hoc DB access from multiple files.
This documentation defines the rules that keep the system stable.

## 2. Repository structure
- backend/
  - main.py: backend server entrypoint
  - db.py: single source of truth for DB connections, schema init, and core queries
  - schema.sql: the database schema
  - seed.py: inserts initial data (optional)
- db/
  - Lager_live.db: the live SQLite file used by the backend
- frontend/
  - api.js: frontend calls to backend endpoints
  - admin.js: admin UI logic (permissions should be enforced server-side)
- scripts/
  - import_*.py: one-off import utilities for CSV/Excel
- data/
  - input exports and generated assets

## 3. The non-negotiable rules
1) All DB connections must come from backend/db.py (get_conn or db_session).
2) schema changes happen only by editing backend/schema.sql, then reapplying with init_db on a new DB.
3) Queries must only select columns that exist in schema.sql.
4) Every write operation must run inside db_session() so commit/rollback is deterministic.
5) Admin checks must be enforced in backend, never only in frontend.

## 4. Database schema overview
Products table is intentionally minimal:
- products.id (integer primary key)
- products.nc_nummer (unique text)
- products.materialkurztext (text)
- products.active (0 or 1)

This means queries must NOT reference:
- kind
- product_name
unless you add those columns in schema.sql (not planned).

## 5. DB initialization
backend/db.py provides init_db().
init_db() applies backend/schema.sql to the DB file.

Expected behavior:
- If db/Lager_live.db exists: init_db() ensures required tables exist.
- If schema.sql is missing or invalid: init_db() fails fast.
- If DB path is wrong: init_db() fails fast.

## 6. Safe DB changes (migration discipline without a migration framework)
This repo currently uses schema.sql as the authoritative schema.
To change the DB safely:
1) Update backend/schema.sql.
2) Create a fresh DB file and run init_db() on it.
3) Run seed/import scripts against the fresh DB.
4) Run the backend and verify frontend endpoints.

Do not “patch” the live DB manually without recording what changed.

## 7. Debugging checklist
- Query error "no such column": schema.sql does not match the query. Fix the query or the schema.
- Empty DB behavior: DB path is wrong and a new empty DB got created. db.py prevents this by failing fast.
- Partial writes: ensure the code is inside db_session().
- Admin logic bypass: frontend checks are not security. enforce server-side checks.

## 8. File dictionary
backend/db.py
- get_conn(): opens sqlite connection with enforced pragmas
- db_session(): transaction wrapper with commit/rollback/close
- init_db(): applies schema.sql
- list_products(): correct product listing query

backend/schema.sql
- defines all tables and constraints

backend/main.py
- starts the server
- calls init_db() at startup
- defines endpoints used by frontend/api.js

## Products columns contract
The backend and frontend assume these columns exist in `products`:
- id
- kind
- nc_nummer
- materialkurztext
- product_name
- active

If you change any of these, you must:
1) update backend/schema.sql
2) run a DB migration on db/Lager_live.db
3) update every SELECT/INSERT/UPDATE referencing products
4) verify frontend tables and sorting

## Minimal migration policy
This repo uses direct SQLite migrations via `sqlite3 db/Lager_live.db`.
Every schema change must be written as a copy pasteable SQL block and stored in docs/DB_CHANGES.md.
