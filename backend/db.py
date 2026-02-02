import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db" / "Lager_live.db"

SITE_TO_LAGER_ID = {
    "konstanz": 1,
    "sindelfingen": 2,
}

def lager_id_from_site(site: str) -> int:
    s = (site or "").lower().strip()
    if s not in SITE_TO_LAGER_ID:
        raise ValueError("Invalid site")
    return SITE_TO_LAGER_ID[s]

def get_conn() -> sqlite3.Connection:
    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON;")
    return con
