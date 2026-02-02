from __future__ import annotations

from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_SQL = Path(__file__).resolve().with_name("schema.sql")
DB_PATH = ROOT / "db" / "Lager_live.db"


def ensure_schema(con: sqlite3.Connection) -> None:
    con.execute("PRAGMA foreign_keys = ON;")
    con.executescript(SCHEMA_SQL.read_text(encoding="utf-8"))


def ensure_lagers(con: sqlite3.Connection) -> None:
    # Stable IDs: 1=Konstanz, 2=Sindelfingen
    con.execute("INSERT OR IGNORE INTO lagers(id, name) VALUES (1, 'konstanz')")
    con.execute("INSERT OR IGNORE INTO lagers(id, name) VALUES (2, 'sindelfingen')")


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row
    try:
        ensure_schema(con)
        ensure_lagers(con)
        con.commit()
    finally:
        con.close()

    print(f"OK: ensured schema + lagers in {DB_PATH}")


if __name__ == "__main__":
    main()
