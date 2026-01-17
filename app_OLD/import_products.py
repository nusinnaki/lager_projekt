import sqlite3
import pandas as pd
from pathlib import Path

XLSX = Path("data/MaterialnachbestellungPopsite_2025_12_02.xlsx")
DB = Path("db/live.db")

TARGET = "Materialkurztext"

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

def main():
    if not XLSX.exists():
        raise FileNotFoundError(XLSX)

    df = read_with_detected_header(XLSX)

    if TARGET in df.columns:
        col = TARGET
        print(f"Using column '{TARGET}' (detected as header).")
    else:
        col = pick_fallback_text_column(df)
        print(f"Column '{TARGET}' not found as header. Falling back to '{col}'.")

    names = (
        df[col]
        .dropna()
        .astype(str)
        .map(lambda x: x.strip())
        .replace({"nan": ""})
    )
    names = [n for n in names if n]

    con = sqlite3.connect(DB)
    cur = con.cursor()

    for name in names:
        cur.execute("INSERT OR IGNORE INTO products(name) VALUES (?)", (name,))
    con.commit()

    cur.execute("SELECT id FROM products")
    product_ids = [r[0] for r in cur.fetchall()]
    for pid in product_ids:
        cur.execute("INSERT OR IGNORE INTO stock(product_id, quantity) VALUES (?, 0)", (pid,))
    con.commit()

    print(f"Imported {len(names)} rows into products.")
    print(f"Products in DB: {cur.execute('SELECT COUNT(*) FROM products').fetchone()[0]}")
    con.close()

if __name__ == "__main__":
    main()
