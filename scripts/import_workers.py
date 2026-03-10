from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db" / "Lager_live.db"
CSV_PATH = ROOT / "data" / "workers.csv"


def norm(x: str | None) -> str:
    return " ".join((x or "").split()).strip()


def main() -> None:
    if not CSV_PATH.exists():
        raise SystemExit(f"workers.csv not found: {CSV_PATH}")

    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON;")

    inserted = 0
    reactivated = 0
    unchanged = 0
    deactivated = 0

    try:
        con.execute("BEGIN")

        with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)

            if reader.fieldnames != ["first_name", "last_name"]:
                raise SystemExit("workers.csv must have header: first_name,last_name")

            csv_workers: list[tuple[str, str]] = []

            for row in reader:
                first = norm(row["first_name"])
                last = norm(row["last_name"])

                if not first or not last:
                    continue

                csv_workers.append((first, last))

        seen = set()
        unique_csv_workers: list[tuple[str, str]] = []
        for worker in csv_workers:
            if worker not in seen:
                seen.add(worker)
                unique_csv_workers.append(worker)

        for first, last in unique_csv_workers:
            existing = con.execute(
                """
                SELECT id, active
                FROM workers
                WHERE first_name = ? AND last_name = ?
                """,
                (first, last),
            ).fetchone()

            if existing:
                if int(existing["active"]) != 1:
                    con.execute(
                        """
                        UPDATE workers
                        SET active = 1
                        WHERE id = ?
                        """,
                        (existing["id"],),
                    )
                    reactivated += 1
                else:
                    unchanged += 1
            else:
                con.execute(
                    """
                    INSERT INTO workers(first_name, last_name, active)
                    VALUES (?, ?, 1)
                    """,
                    (first, last),
                )
                inserted += 1

        csv_name_set = set(unique_csv_workers)

        db_workers = con.execute(
            """
            SELECT id, first_name, last_name, active
            FROM workers
            """
        ).fetchall()

        for row in db_workers:
            key = (row["first_name"], row["last_name"])
            if key not in csv_name_set and int(row["active"]) != 0:
                con.execute(
                    """
                    UPDATE workers
                    SET active = 0
                    WHERE id = ?
                    """,
                    (row["id"],),
                )
                deactivated += 1

        con.commit()

    except Exception:
        con.rollback()
        raise

    finally:
        con.close()

    print(f"Inserted new workers: {inserted}")
    print(f"Reactivated workers: {reactivated}")
    print(f"Unchanged active workers: {unchanged}")
    print(f"Deactivated missing workers: {deactivated}")


if __name__ == "__main__":
    main()