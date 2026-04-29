from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db" / "Lager_live.db"
CSV_PATH = ROOT / "data" / "sites.csv"


def main() -> None:
    if not CSV_PATH.exists():
        raise SystemExit(f"sites.csv not found: {CSV_PATH}")

    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row

    inserted = 0

    try:
        con.execute("BEGIN")

        with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)

            for row in reader:
                name = (row.get("name") or "").strip()
                if not name:
                    continue

                cur = con.execute(
                    """
                    INSERT OR IGNORE INTO sites(name, active)
                    VALUES (?, 1)
                    """,
                    (name,),
                )

                if cur.rowcount:
                    inserted += 1

        con.commit()

    except Exception:
        con.rollback()
        raise

    finally:
        con.close()

    print(f"Inserted sites: {inserted}")


if __name__ == "__main__":
    main()