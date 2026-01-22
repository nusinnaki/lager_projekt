from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
WORKERS_CSV = DATA_DIR / "workers.csv"
PRODUCTS_MASTER = DATA_DIR / "products_master.csv"

def norm(x) -> str:
    return " ".join(str(x or "").replace("\xa0", " ").split()).strip()

def import_workers(con: sqlite3.Connection) -> int:
    if not WORKERS_CSV.exists():
        raise FileNotFoundError(WORKERS_CSV)

    cur = con.cursor()
    cur.execute("DELETE FROM workers;")
    con.commit()

    inserted = 0
    with WORKERS_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or "name" not in reader.fieldnames:
            raise ValueError("data/workers.csv must have header: name")
        for row in reader:
            name = norm(row.get("name"))
            if not name:
                continue
            cur.execute("INSERT OR IGNORE INTO workers(name, active) VALUES (?, 1)", (name,))
            inserted += cur.rowcount

    con.commit()
    return inserted

def import_products(con: sqlite3.Connection) -> int:
    if not PRODUCTS_MASTER.exists():
        raise FileNotFoundError(PRODUCTS_MASTER)

    cur = con.cursor()
    cur.execute("DELETE FROM logs;")
    cur.execute("DELETE FROM stock;")
    cur.execute("DELETE FROM products;")
    con.commit()

    inserted = 0
    with PRODUCTS_MASTER.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        needed = {"product_source", "product_name", "internal_id", "qr_code"}
        if not reader.fieldnames or not needed.issubset(set(reader.fieldnames)):
            raise ValueError("data/products_master.csv must have columns: product_source,product_name,internal_id,qr_code")
        for row in reader:
            ps = norm(row.get("product_source"))
            pn = norm(row.get("product_name"))
            iid = norm(row.get("internal_id"))
            qr = norm(row.get("qr_code"))
            if not (pn and iid and qr):
                continue
            cur.execute(
                "INSERT INTO products(product_source, product_name, internal_id, qr_code) VALUES (?, ?, ?, ?)",
                (ps, pn, iid, qr),
            )
            inserted += 1

    con.commit()

    cur.execute("SELECT id FROM products;")
    for (pid,) in cur.fetchall():
        cur.execute("INSERT OR IGNORE INTO stock(product_id, quantity) VALUES (?, 0)", (pid,))
    con.commit()

    return inserted

def main(db_path: str) -> None:
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA foreign_keys = ON;")
    tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()}
    needed = {"workers", "products", "stock", "logs"}
    missing = needed - tables
    if missing:
        raise SystemExit(f"{db_path}: missing tables {missing}. Apply backend/schema.sql first.")

    w = import_workers(con)
    p = import_products(con)
    print(f"{db_path}: workers={w}, products={p}")
    con.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python3 backend/import_data.py <db_path>")
    main(sys.argv[1])
