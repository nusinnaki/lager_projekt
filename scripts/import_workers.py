from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db" / "Lager_live.db"
WORKERS_CSV = ROOT / "data" / "workers.csv"


def main() -> None:
    if not WORKERS_CSV.exists():
        raise SystemExit(f"workers.csv not found at {WORKERS_CSV}")

    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON;")

    inserted = 0

    with WORKERS_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise SystemExit("workers.csv has no header")
        if "name" not in reader.fieldnames:
            raise SystemExit("workers.csv must contain a 'name' column")

        for row in reader:
            name = " ".join((row.get("name") or "").split()).strip()
            if not name:
                continue

            cur = con.execute(
                "INSERT OR IGNORE INTO workers(name, active) VALUES (?, 1)",
                (name,),
            )
            inserted += cur.rowcount

    con.commit()
    con.close()
    print(f"OK: inserted {inserted} workers")


if __name__ == "__main__":
    main()
