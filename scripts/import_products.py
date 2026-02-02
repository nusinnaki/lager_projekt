#!/usr/bin/env python3
from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db" / "Lager_live.db"
CSV_PATH = ROOT / "data" / "products.csv"

LAGERS = [1, 2]  # 1=konstanz, 2=sindelfingen


def main() -> None:
    if not CSV_PATH.exists():
        raise FileNotFoundError(CSV_PATH)

    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON;")

    inserted_products = 0
    ensured_stock = 0

    try:
        con.execute("BEGIN;")

        with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
            r = csv.DictReader(f)
            if not r.fieldnames:
                raise SystemExit("products.csv has no header")

            hdr = {h.strip().lower(): h.strip() for h in r.fieldnames if h}
            k_nc = hdr.get("nc_nummer") or hdr.get("nc-nummer") or hdr.get("ncnummer")
            k_txt = hdr.get("materialkurztext") or hdr.get("material_kurztext")

            if not k_nc or not k_txt:
                raise SystemExit("products.csv must have headers: NC_Nummer and Materialkurztext")

            for row in r:
                nc = (row.get(k_nc) or "").strip()
                txt = " ".join((row.get(k_txt) or "").split()).strip()
                if not nc or not txt:
                    continue

                cur = con.execute(
                    "INSERT OR IGNORE INTO products(nc_nummer, materialkurztext, active) VALUES (?, ?, 1)",
                    (nc, txt),
                )
                inserted_products += cur.rowcount

                # get product_id (existing or new)
                pid_row = con.execute(
                    "SELECT id FROM products WHERE nc_nummer=?",
                    (nc,),
                ).fetchone()
                pid = int(pid_row["id"])

                # ensure stock rows for both lagers
                for lager_id in LAGERS:
                    cur2 = con.execute(
                        "INSERT OR IGNORE INTO stock(lager_id, product_id, quantity) VALUES (?, ?, 0)",
                        (lager_id, pid),
                    )
                    ensured_stock += cur2.rowcount

        con.commit()
        print(f"OK: inserted {inserted_products} products, ensured {ensured_stock} stock rows")
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


if __name__ == "__main__":
    main()
