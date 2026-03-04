# DB Changes Guide

## Goal
Avoid silent breakage when schema or queries change.

## Common failure mode
A query selects a column that does not exist in the DB.
Example: SELECT kind FROM products when products.kind does not exist.

## Enforced policy
- schema is defined in backend/schema.sql
- queries must match schema.sql exactly
- DB access is only through backend/db.py

## Workflow for changing schema
1) Edit backend/schema.sql
2) Build a fresh DB:
   - move old DB aside
   - create new db/Lager_live.db
   - run init_db()
3) Reimport data using scripts/ imports
4) Verify endpoints and frontend

## What not to do
- Do not add columns directly in a live DB without updating schema.sql
- Do not copy SQL snippets around the repo; centralize in db.py
