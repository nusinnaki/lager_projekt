from __future__ import annotations

from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_SQL = ROOT / "backend" / "schema.sql"
DB_PATH = ROOT / "db" / "Lager_live.db"


def ensure_schema(con: sqlite3.Connection) -> None:
    if not SCHEMA_SQL.exists():
        raise RuntimeError(f"schema.sql not found: {SCHEMA_SQL}")

    con.execute("PRAGMA foreign_keys = ON;")
    con.execute("PRAGMA journal_mode = WAL;")
    con.execute("PRAGMA synchronous = NORMAL;")

    sql = SCHEMA_SQL.read_text(encoding="utf-8").strip()
    if not sql:
        raise RuntimeError("schema.sql is empty")

    con.executescript(sql)


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    con = sqlite3.connect(str(DB_PATH))
    try:
        ensure_schema(con)
        con.commit()
    finally:
        con.close()

    print(f"OK: ensured schema in {DB_PATH}")


if __name__ == "__main__":
    main()