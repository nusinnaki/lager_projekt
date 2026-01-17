import csv
import sqlite3
from pathlib import Path

CSV_PATH = Path("data/workers.csv")
DB = Path("db/live.db")

def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(CSV_PATH)

    con = sqlite3.connect(DB)
    cur = con.cursor()

    with open(CSV_PATH, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name = (row.get("name") or "").strip()
            if name:
                cur.execute("INSERT OR IGNORE INTO workers(name, active) VALUES (?, 1)", (name,))
    con.commit()

    print(f"Workers in DB: {cur.execute('SELECT COUNT(*) FROM workers').fetchone()[0]}")
    con.close()

if __name__ == "__main__":
    main()

