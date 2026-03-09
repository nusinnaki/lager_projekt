from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db" / "Lager_live.db"
WORKERS_CSV = ROOT / "data" / "workers.csv"


def norm(x: str | None) -> str:
    return " ".join((x or "").replace("\xa0", " ").split()).strip()


def split_name(full_name: str) -> tuple[str, str]:
    parts = norm(full_name).split()
    if len(parts) < 2:
        raise ValueError(f"Cannot split worker name into first_name/last_name: {full_name!r}")
    first_name = parts[0]
    last_name = " ".join(parts[1:])
    return first_name, last_name


def main() -> None:
    if not WORKERS_CSV.exists():
        raise SystemExit(f"workers.csv not found at {WORKERS_CSV}")

    if not DB_PATH.exists():
        raise SystemExit(f"DB not found at {DB_PATH}")

    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON;")

    inserted = 0

    try:
        con.execute("BEGIN;")

        # If workers already exist and logs reference them, clear logs first
        con.execute("DELETE FROM logs;")
        con.execute("DELETE FROM workers;")

        with WORKERS_CSV.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                raise SystemExit("workers.csv has no header")

            headers = {h.strip().lower(): h.strip() for h in reader.fieldnames if h}

            k_first = headers.get("first_name") or headers.get("firstname") or headers.get("first name")
            k_last = headers.get("last_name") or headers.get("lastname") or headers.get("last name")
            k_name = headers.get("name")

            if not ((k_first and k_last) or k_name):
                raise SystemExit(
                    "workers.csv must contain either:\n"
                    "- first_name,last_name\n"
                    "or\n"
                    "- name"
                )

            for row in reader:
                if k_first and k_last:
                    first_name = norm(row.get(k_first))
                    last_name = norm(row.get(k_last))
                else:
                    full_name = norm(row.get(k_name))
                    if not full_name:
                        continue
                    first_name, last_name = split_name(full_name)

                if not first_name or not last_name:
                    continue

                cur = con.execute(
                    """
                    INSERT INTO workers(first_name, last_name, active)
                    VALUES (?, ?, 1)
                    """,
                    (first_name, last_name),
                )
                inserted += cur.rowcount

        con.commit()
        print(f"OK: inserted {inserted} workers")

    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


if __name__ == "__main__":
    main()