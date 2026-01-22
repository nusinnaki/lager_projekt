import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DB_MAP = {
    "konstanz": ROOT / "db" / "Konstanz_Lager_live.db",
    "sindelfingen": ROOT / "db" / "Sindelfingen_Lager_live.db",
}

def get_conn(site: str) -> sqlite3.Connection:
    site = (site or "").lower().strip()
    if site not in DB_MAP:
        raise ValueError("Invalid site")
    con = sqlite3.connect(DB_MAP[site])
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON;")
    return con
