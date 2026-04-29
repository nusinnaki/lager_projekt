from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

from passlib.context import CryptContext

ROOT = Path(__file__).resolve().parents[1]

DB_PATH = ROOT / "db" / "Lager_live.db"
CSV_PATH = ROOT / "data" / "workers.csv"

DEFAULT_PASSWORD = "popsite1234"

FIRST_ADMINS = {
    ("nusin", "naki"),
    ("hannes", ""),
    ("dominik", ""),
    ("daniel", ""),
    ("martin", ""),
}

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def norm(x: str | None) -> str:
    return " ".join((x or "").split()).strip()


def username_from_worker(first_name: str, last_name: str) -> str:
    first = first_name.strip().lower().replace(" ", "")
    last = last_name.strip().lower().replace(" ", "")
    return f"{first}.{last}"


def unique_username(con: sqlite3.Connection, base: str) -> str:
    candidate = base
    n = 2

    while True:
        row = con.execute(
            """
            SELECT id
            FROM workers
            WHERE username = ?
            """,
            (candidate,),
        ).fetchone()

        if not row:
            return candidate

        candidate = f"{base}{n}"
        n += 1


def is_first_admin(first_name: str, last_name: str) -> bool:
    first = first_name.strip().casefold()
    last = last_name.strip().casefold()

    if (first, last) in FIRST_ADMINS:
        return True

    if (first, "") in FIRST_ADMINS:
        return True

    return False


def main() -> None:
    if not CSV_PATH.exists():
        raise SystemExit(f"workers.csv not found: {CSV_PATH}")

    if not DB_PATH.exists():
        raise SystemExit(f"DB not found: {DB_PATH}")

    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON;")

    inserted = 0
    reactivated = 0
    unchanged = 0
    deactivated = 0
    admins_set = 0

    try:
        con.execute("BEGIN")

        with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)

            expected = ["first_name", "last_name"]

            if reader.fieldnames != expected:
                raise SystemExit(
                    "workers.csv must have header: first_name,last_name"
                )

            csv_workers: list[tuple[str, str]] = []

            for row in reader:
                first = norm(row["first_name"])
                last = norm(row["last_name"])

                if not first or not last:
                    continue

                csv_workers.append((first, last))

        seen = set()
        unique_csv_workers: list[tuple[str, str]] = []

        for first, last in csv_workers:
            key = (first.casefold(), last.casefold())

            if key in seen:
                continue

            seen.add(key)
            unique_csv_workers.append((first, last))

        for first, last in unique_csv_workers:
            existing = con.execute(
                """
                SELECT
                    id,
                    username,
                    password_hash,
                    is_active,
                    is_admin
                FROM workers
                WHERE first_name = ?
                  AND last_name = ?
                """,
                (first, last),
            ).fetchone()

            is_admin = 1 if is_first_admin(first, last) else 0

            password_hash = (
                pwd.hash(DEFAULT_PASSWORD)
                if is_admin == 1
                else None
            )

            if existing:
                con.execute(
                    """
                    UPDATE workers
                    SET
                        is_active = 1,
                        auth_provider = 'local',
                        password_hash = CASE
                            WHEN ? = 1 AND password_hash IS NULL
                            THEN ?
                            ELSE password_hash
                        END,
                        is_admin = ?
                    WHERE id = ?
                    """,
                    (
                        is_admin,
                        password_hash,
                        is_admin,
                        existing["id"],
                    ),
                )

                if is_admin == 1 and int(existing["is_admin"]) != 1:
                    admins_set += 1

                if int(existing["is_active"]) != 1:
                    reactivated += 1
                else:
                    unchanged += 1

            else:
                base_username = username_from_worker(first, last)
                username = unique_username(con, base_username)

                con.execute(
                    """
                    INSERT INTO workers(
                        first_name,
                        last_name,
                        username,
                        password_hash,
                        auth_provider,
                        ldap_dn,
                        is_admin,
                        is_active
                    )
                    VALUES (?, ?, ?, ?, 'local', NULL, ?, 1)
                    """,
                    (
                        first,
                        last,
                        username,
                        password_hash,
                        is_admin,
                    ),
                )

                if is_admin == 1:
                    admins_set += 1

                inserted += 1

        csv_name_set = {
            (first, last)
            for first, last in unique_csv_workers
        }

        db_workers = con.execute(
            """
            SELECT
                id,
                first_name,
                last_name,
                is_active
            FROM workers
            """
        ).fetchall()

        for row in db_workers:
            key = (
                row["first_name"],
                row["last_name"],
            )

            if key not in csv_name_set and int(row["is_active"]) != 0:
                con.execute(
                    """
                    UPDATE workers
                    SET is_active = 0
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
    print(f"Admins assigned: {admins_set}")
    print(f"Default password for admins only: {DEFAULT_PASSWORD}")


if __name__ == "__main__":
    main()