from pathlib import Path
import sqlite3
from passlib.context import CryptContext

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db" / "Lager_live.db"

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

TEMP_PASSWORD = "popsite1234"


def username(first, last):
    return f"{first.strip().lower()}.{last.strip().lower()}"


def main():

    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row

    password_hash = pwd.hash(TEMP_PASSWORD)

    workers = con.execute(
        """
        SELECT id, first_name, last_name
        FROM workers
        WHERE active = 1
        """
    ).fetchall()

    created = 0

    for w in workers:

        uname = username(w["first_name"], w["last_name"])

        exists = con.execute(
            "SELECT id FROM users WHERE worker_id = ?",
            (w["id"],),
        ).fetchone()

        if exists:
            continue

        is_admin = 1 if uname == "nusin.naki" else 0

        con.execute(
            """
            INSERT INTO users(
                worker_id,
                username,
                password_hash,
                is_admin,
                is_active
            )
            VALUES (?, ?, ?, ?, 1)
            """,
            (
                w["id"],
                uname,
                password_hash,
                is_admin,
            ),
        )

        created += 1

    con.commit()
    con.close()

    print(f"Created {created} user accounts")
    print(f"Temporary password: {TEMP_PASSWORD}")


if __name__ == "__main__":
    main()