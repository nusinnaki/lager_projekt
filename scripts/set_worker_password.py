#!/usr/bin/env python3
from __future__ import annotations

import sqlite3
from pathlib import Path
from passlib.context import CryptContext

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db" / "Lager_live.db"

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit(f"DB not found: {DB_PATH}")

    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row

    rows = con.execute("""
        SELECT id, first_name, last_name, username
        FROM workers
        ORDER BY id
    """).fetchall()

    if not rows:
        print("No workers found.")
        return

    print("\nWorkers:\n")
    for r in rows:
        print(f"{r['id']}: {r['first_name']} {r['last_name']} (username='{r['username']}')")

    worker_id = int(input("\nWorker ID: ").strip())
    username = input("Username: ").strip()
    password = input("Password: ").strip()

    if not username or not password:
        print("Username and password required.")
        return

    password_hash = pwd.hash(password)

    con.execute("""
        UPDATE workers
        SET username = ?, password_hash = ?, auth_provider = 'local', is_active = 1, is_admin = 1
        WHERE id = ?
    """, (username, password_hash, worker_id))

    con.commit()
    con.close()

    print("\nOK: login updated.")


if __name__ == "__main__":
    main()