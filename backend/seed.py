cat > backend/seed.py <<'EOF'
from __future__ import annotations

from pathlib import Path
import csv
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
WORKERS_CSV = DATA_DIR / "workers.csv"
PRODUCTS_XLSX = DATA_DIR / "MaterialnachbestellungPopsite_2025_12_02.xlsx"

def _ensure_tables(con: sqlite3.Connection) -> None:
    cur = con.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS workers (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL UNIQUE,
      active INTEGER NOT NULL DEFAULT 1
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL UNIQUE
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS stock (
      product_id INTEGER PRIMARY KEY,
      quantity INTEGER NOT NULL DEFAULT 0,
      FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS logs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      ts TEXT NOT NULL,
      action TEXT NOT NULL CHECK(action IN ('TAKE','LOAD')),
      worker_id INTEGER NOT NULL,
      product_id INTEGER NOT NULL,
      quantity INTEGER NOT NULL CHECK(quantity > 0),
      delta INTEGER NOT NULL,
      FOREIGN KEY(worker_id) REFERENCES workers(id),
      FOREIGN KEY(product_id) REFERENCES products(id)
    );
    """)

    cur.execute("CREATE INDEX IF NOT EXISTS idx_logs_ts ON logs(ts);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_logs_worker ON logs(worker_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_logs_product ON logs(product_id);")
    con.commit()

def _import_workers(con: sqlite3.Connection) -> int:
    if not WORKERS_CSV.exists():
        return 0

    cur = con.cursor()
    inserted = 0

    with WORKERS_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("name") or "").strip()
            if not name:
                continue
            cur.execute("INSERT OR IGNORE INTO workers(name, active) VALUES (?, 1)", (name,))
            inserted += cur.rowcount

    con.commit()
    return inserted

def _extract_product_names_from_excel() -> list[str]:
    if not PRODUCTS_XLSX.exists():
        return []

    df = pd.read_excel(PRODUCTS_XLSX, engine="openpyxl")

    # Your Excel does not have a clean "Materialkurztext" header right now.
    # Robust approach: take the first column as the product-name column.
    col0 = df.columns[0]
    series = df[col0].dropna().astype(str)

    names: list[str] = []
    seen = set()

    for v in series:
        s = " ".join(v.replace("\xa0", " ").split()).strip()
        if not s:
            continue
        if s.lower() in ("nan", "none"):
            continue
        if s not in seen:
            seen.add(s)
            names.append(s)

    return names

def _import_products(con: sqlite3.Connection) -> int:
    cur = con.cursor()
    names = _extract_product_names_from_excel()
    if not names:
        return 0

    inserted = 0
    for name in names:
        cur.execute("INSERT OR IGNORE INTO products(name) VALUES (?)", (name,))
        inserted += cur.rowcount
    con.commit()

    # Ensure stock rows exist
    cur.execute("SELECT id FROM products")
    product_ids = [r[0] for r in cur.fetchall()]
    for pid in product_ids:
        cur.execute("INSERT OR IGNORE INTO stock(product_id, quantity) VALUES (?, 0)", (pid,))
    con.commit()

    return inserted

def ensure_seeded(con: sqlite3.Connection) -> None:
    _ensure_tables(con)

    cur = con.cursor()
    w_count = cur.execute("SELECT COUNT(*) FROM workers").fetchone()[0]
    p_count = cur.execute("SELECT COUNT(*) FROM products").fetchone()[0]

    # Seed only if empty to avoid accidental duplication or overwriting.
    if w_count == 0:
        _import_workers(con)
    if p_count == 0:
        _import_products(con)
EOF
