from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
WORKERS_CSV = DATA_DIR / "workers.csv"
PRODUCTS_XLSX = DATA_DIR / "MaterialnachbestellungPopsite_2025_12_02.xlsx"

TARGET = "Materialkurztext"

def norm(x) -> str:
    return " ".join(str(x).replace("\xa0", " ").split()).strip()

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
            raise ValueError("data/workers.csv must have a header column: name")
        for row in reader:
            name = norm(row.get("name", ""))
            if not name:
                continue
            cur.execute("INSERT OR IGNORE INTO workers(name, active) VALUES (?, 1)", (name,))
            inserted += cur.rowcount

    con.commit()
    return inserted

def read_with_detected_header(path: Path) -> pd.DataFrame:
    # First try normal header reading
    df = pd.read_excel(path, engine="openpyxl")
    df.columns = [str(c).strip() for c in df.columns]
    if TARGET in df.columns:
        return df

    # If not present, scan top rows without header to find a row containing TARGET
    raw = pd.read_excel(path, engine="openpyxl", header=None)
    max_scan = min(30, len(raw))

    header_row = None
    for r in range(max_scan):
        row_vals = raw.iloc[r].astype(str).map(lambda x: x.strip()).tolist()
        if any(v == TARGET for v in row_vals):
            header_row = r
            break

    if header_row is None:
        # fallback: return the first df; caller may choose another column
        return df

    # Re-read using the detected header row
    df2 = pd.read_excel(path, engine="openpyxl", header=header_row)
    df2.columns = [str(c).strip() for c in df2.columns]
    return df2

def pick_fallback_text_column(df: pd.DataFrame) -> str:
    # choose the best text-like column if TARGET still not present
    best_col = None
    best_score = -1
    for col in df.columns:
        s = df[col].dropna().astype(str).map(lambda x: x.strip())
        s = s[s != ""]
        if s.empty:
            continue
        avg_len = s.map(len).mean()
        numeric_like = s.str.fullmatch(r"[0-9\.,\- ]+").mean() if len(s) else 0
        score = avg_len - (numeric_like * 50)
        if score > best_score:
            best_score = score
            best_col = col
    if best_col is None:
        raise ValueError("Could not detect a usable product column.")
    return str(best_col)

def extract_product_names() -> list[str]:
    if not PRODUCTS_XLSX.exists():
        raise FileNotFoundError(PRODUCTS_XLSX)

    df = read_with_detected_header(PRODUCTS_XLSX)

    if TARGET in df.columns:
        col = TARGET
        print(f"Using column '{TARGET}' (detected as header).")
    else:
        col = pick_fallback_text_column(df)
        print(f"Column '{TARGET}' not found as header. Falling back to '{col}'.")

    s = (
        df[col]
        .dropna()
        .astype(str)
        .map(norm)
        .replace({"nan": ""})
    )
    names = [x for x in s.tolist() if x]
    return names

def import_products(con: sqlite3.Connection) -> int:
    names = extract_product_names()
    cur = con.cursor()

    cur.execute("DELETE FROM logs;")
    cur.execute("DELETE FROM stock;")
    cur.execute("DELETE FROM products;")
    con.commit()

    inserted = 0
    for name in names:
        cur.execute("INSERT OR IGNORE INTO products(name) VALUES (?)", (name,))
        inserted += cur.rowcount
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
