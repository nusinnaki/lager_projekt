from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


# repo root (lager_projekt)
ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db" / "Lager_live.db"
SCHEMA_PATH = ROOT / "backend" / "schema.sql"


class DbConfigError(RuntimeError):
    """Raised when filesystem/config makes DB unusable (missing file, wrong path)."""


class DbConnectionError(RuntimeError):
    """Raised when sqlite cannot open the DB (permissions, corruption, etc.)."""


class DbSchemaError(RuntimeError):
    """Raised when schema.sql is missing or invalid SQL."""


@dataclass(frozen=True)
class DbConfig:
    db_path: Path = DB_PATH
    schema_path: Path = SCHEMA_PATH


def get_conn(cfg: DbConfig = DbConfig()) -> sqlite3.Connection:
    """
    Open a configured sqlite connection.

    Fail fast if:
    - DB file does not exist (prevents silently creating a new empty DB)
    - path exists but is not a file
    - sqlite cannot open it

    Apply:
    - Row factory for dict-like rows
    - foreign keys on
    - WAL journaling for better concurrency
    """
    if not cfg.db_path.exists():
        raise DbConfigError(f"DB file not found: {cfg.db_path}")
    if not cfg.db_path.is_file():
        raise DbConfigError(f"DB path is not a file: {cfg.db_path}")

    try:
        con = sqlite3.connect(str(cfg.db_path))
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON;")
        con.execute("PRAGMA journal_mode = WAL;")
        con.execute("PRAGMA synchronous = NORMAL;")
        return con
    except sqlite3.Error as e:
        raise DbConnectionError(f"Cannot open sqlite DB: {cfg.db_path}") from e


@contextmanager
def db_session(cfg: DbConfig = DbConfig()) -> Iterator[sqlite3.Connection]:
    """
    Transaction wrapper.

    - commit on success
    - rollback on any exception
    - always close
    """
    con = get_conn(cfg)
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def init_db(cfg: DbConfig = DbConfig()) -> None:
    """
    Apply backend/schema.sql to ensure required tables exist.

    Fail fast if schema.sql missing or has SQL errors.
    """
    if not cfg.schema_path.exists():
        raise DbSchemaError(f"schema.sql missing: {cfg.schema_path}")

    sql = cfg.schema_path.read_text(encoding="utf-8")

    with db_session(cfg) as con:
        try:
            con.executescript(sql)
        except sqlite3.Error as e:
            raise DbSchemaError("Failed to apply schema.sql") from e


def lager_id_from_site(site: str) -> int:
    """
    Convert a site string to lager_id.
    """
    s = (site or "").lower().strip()
    mapping = {"konstanz": 1, "sindelfingen": 2}
    if s in mapping:
        return mapping[s]
    allowed = ", ".join(sorted(mapping.keys()))
    raise ValueError(f"Invalid site: {site!r}. Allowed: {allowed}")


def list_products(con: sqlite3.Connection) -> list[dict]:
    """
    Canonical product list query. Must match schema.sql columns.
    """
    rows = con.execute(
        """
        SELECT
          id,
          kind,
          nc_nummer,
          materialkurztext,
          product_name,
          active
        FROM products
        ORDER BY
          kind,
          COALESCE(materialkurztext, product_name, nc_nummer, CAST(id AS TEXT)),
          id;
        """
    ).fetchall()
    return [dict(r) for r in rows]

def list_workers(con: sqlite3.Connection, site: str) -> list[dict]:
    """
    Canonical worker list query for a given site.

    API compatibility: returns `name` (alias of full_name) because the older frontend
    likely expects a `name` key.
    """
    s = (site or "").lower().strip()
    rows = con.execute(
        """
        SELECT
          id,
          full_name AS name,
          site,
          active
        FROM workers
        WHERE lower(site) = ?
        ORDER BY COALESCE(full_name, CAST(id AS TEXT)), id;
        """,
        (s,),
    ).fetchall()
    return [dict(r) for r in rows]
