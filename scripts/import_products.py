#!/usr/bin/env python3
from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db" / "Lager_live.db"
CSV_PATH = ROOT / "data" / "products.csv"

DEFAULT_BRAND = "Netcom"
DEFAULT_CATEGORY = "Other"


def norm(x: str | None) -> str:
    return " ".join((x or "").replace("\xa0", " ").split()).strip()


def get_or_create_brand(con: sqlite3.Connection, name: str) -> int:
    row = con.execute(
        """
        SELECT id
        FROM brands
        WHERE lower(trim(name)) = lower(trim(?))
        """,
        (name,),
    ).fetchone()

    if row:
        con.execute(
            """
            UPDATE brands
            SET active = 1
            WHERE id = ?
            """,
            (row["id"],),
        )
        return int(row["id"])

    cur = con.execute(
        """
        INSERT INTO brands(name, active)
        VALUES (?, 1)
        """,
        (name,),
    )
    return int(cur.lastrowid)


def get_or_create_category(con: sqlite3.Connection, name: str) -> int:
    row = con.execute(
        """
        SELECT id
        FROM categories
        WHERE lower(trim(name)) = lower(trim(?))
        """,
        (name,),
    ).fetchone()

    if row:
        con.execute(
            """
            UPDATE categories
            SET active = 1
            WHERE id = ?
            """,
            (row["id"],),
        )
        return int(row["id"])

    cur = con.execute(
        """
        INSERT INTO categories(name, active)
        VALUES (?, 1)
        """,
        (name,),
    )
    return int(cur.lastrowid)


def main() -> None:
    if not CSV_PATH.exists():
        raise SystemExit(f"products.csv not found: {CSV_PATH}")

    if not DB_PATH.exists():
        raise SystemExit(f"DB not found: {DB_PATH}")

    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON;")

    inserted_products = 0
    skipped_products = 0

    try:
        con.execute("BEGIN")

        with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)

            if not reader.fieldnames:
                raise SystemExit("products.csv has no header")

            hdr = {h.strip().lower(): h.strip() for h in reader.fieldnames if h}

            k_nc = hdr.get("nc_nummer") or hdr.get("nc-nummer") or hdr.get("ncnummer")
            k_name = hdr.get("product_name") or hdr.get("materialkurztext") or hdr.get("material_kurztext")
            k_brand = hdr.get("brand") or hdr.get("marke")
            k_category = hdr.get("category") or hdr.get("kategorie")

            if not k_name:
                raise SystemExit(
                    "products.csv must have a product name column: "
                    "product_name or Materialkurztext"
                )

            for row in reader:
                product_name = norm(row.get(k_name))
                nc = norm(row.get(k_nc)) if k_nc else None
                brand_name = norm(row.get(k_brand)) if k_brand else DEFAULT_BRAND
                category_name = norm(row.get(k_category)) if k_category else DEFAULT_CATEGORY

                if not product_name:
                    skipped_products += 1
                    continue

                if not brand_name:
                    brand_name = DEFAULT_BRAND

                if not category_name:
                    category_name = DEFAULT_CATEGORY

                brand_id = get_or_create_brand(con, brand_name)
                category_id = get_or_create_category(con, category_name)

                cur = con.execute(
                    """
                    INSERT OR IGNORE INTO products(
                        category_id,
                        brand_id,
                        product_name,
                        nc_nummer,
                        active
                    )
                    VALUES (?, ?, ?, ?, 1)
                    """,
                    (category_id, brand_id, product_name, nc or None),
                )

                if cur.rowcount:
                    inserted_products += 1
                else:
                    skipped_products += 1

        con.commit()

    except Exception:
        con.rollback()
        raise

    finally:
        con.close()

    print(
        f"OK: inserted {inserted_products} products, "
        f"skipped {skipped_products} existing/invalid rows"
    )


if __name__ == "__main__":
    main()