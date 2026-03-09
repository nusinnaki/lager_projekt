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
    """Raised when filesystem/config makes DB unusable."""


class DbConnectionError(RuntimeError):
    """Raised when sqlite cannot open the DB."""


class DbSchemaError(RuntimeError):
    """Raised when schema.sql is missing, empty, or invalid."""


@dataclass(frozen=True)
class DbConfig:
    db_path: Path = DB_PATH
    schema_path: Path = SCHEMA_PATH


def get_conn(cfg: DbConfig = DbConfig()) -> sqlite3.Connection:
    """
    Open a configured sqlite connection.

    Fail fast if:
    - parent DB directory does not exist
    - DB path exists but is not a file

    Apply:
    - Row factory for dict-like rows
    - foreign keys on
    - WAL journaling for better concurrency
    """
    db_dir = cfg.db_path.parent

    if not db_dir.exists():
        raise DbConfigError(f"DB directory not found: {db_dir}")

    if cfg.db_path.exists() and not cfg.db_path.is_file():
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

    Fail fast if schema.sql is missing, empty, or has SQL errors.
    """
    if not cfg.schema_path.exists():
        raise DbSchemaError(f"schema.sql missing: {cfg.schema_path}")

    sql = cfg.schema_path.read_text(encoding="utf-8").strip()
    if not sql:
        raise DbSchemaError(f"schema.sql is empty: {cfg.schema_path}")

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


def site_from_lager_id(lager_id: int) -> str:
    """
    Convert lager_id back to site string.
    """
    mapping = {1: "konstanz", 2: "sindelfingen"}
    if lager_id in mapping:
        return mapping[lager_id]
    allowed = ", ".join(str(k) for k in sorted(mapping.keys()))
    raise ValueError(f"Invalid lager_id: {lager_id!r}. Allowed: {allowed}")


def username_from_worker(first_name: str, last_name: str) -> str:
    """
    Build login username as first.last in lowercase.
    """
    first = first_name.strip().lower().replace(" ", "")
    last = last_name.strip().lower().replace(" ", "")
    return f"{first}.{last}"


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
          product_name,
          active
        FROM products
        ORDER BY
          kind,
          COALESCE(product_name, nc_nummer, CAST(id AS TEXT)),
          id;
        """
    ).fetchall()
    return [dict(r) for r in rows]


def list_workers(con: sqlite3.Connection) -> list[dict]:
    """
    Canonical worker list query.

    Returns:
    - id
    - name (first_name + last_name)
    - first_name
    - last_name
    - active
    """
    rows = con.execute(
        """
        SELECT
          id,
          first_name,
          last_name,
          first_name || ' ' || last_name AS name,
          active
        FROM workers
        ORDER BY
          last_name,
          first_name,
          id;
        """
    ).fetchall()
    return [dict(r) for r in rows]


def get_user_by_username(con: sqlite3.Connection, username: str) -> dict | None:
    """
    Fetch one user by username, joined with worker display data.
    """
    row = con.execute(
        """
        SELECT
          u.id,
          u.worker_id,
          u.username,
          u.password_hash,
          u.is_admin,
          u.is_active,
          u.password_set_at,
          u.created_at,
          w.first_name,
          w.last_name
        FROM users u
        JOIN workers w ON w.id = u.worker_id
        WHERE u.username = ?
        """,
        (username,),
    ).fetchone()
    return dict(row) if row else None


def get_user_by_id(con: sqlite3.Connection, user_id: int) -> dict | None:
    """
    Fetch one user by user id, joined with worker display data.
    """
    row = con.execute(
        """
        SELECT
          u.id,
          u.worker_id,
          u.username,
          u.password_hash,
          u.is_admin,
          u.is_active,
          u.password_set_at,
          u.created_at,
          w.first_name,
          w.last_name
        FROM users u
        JOIN workers w ON w.id = u.worker_id
        WHERE u.id = ?
        """,
        (user_id,),
    ).fetchone()
    return dict(row) if row else None


def list_users(con: sqlite3.Connection) -> list[dict]:
    """
    Canonical user list query for admin use.
    """
    rows = con.execute(
        """
        SELECT
          u.id,
          u.worker_id,
          u.username,
          u.is_admin,
          u.is_active,
          u.password_set_at,
          u.created_at,
          w.first_name,
          w.last_name
        FROM users u
        JOIN workers w ON w.id = u.worker_id
        ORDER BY
          w.last_name,
          w.first_name,
          u.id
        """
    ).fetchall()
    return [dict(r) for r in rows]


def list_stock_for_lager(con: sqlite3.Connection, lager_id: int) -> list[dict]:
    """
    Canonical stock query for a single lager.
    """
    rows = con.execute(
        """
        SELECT
          p.id AS product_id,
          p.kind,
          p.nc_nummer,
          p.product_name,
          p.active,
          s.quantity
        FROM stock s
        JOIN products p ON p.id = s.product_id
        WHERE s.lager_id = ?
        ORDER BY
          p.kind,
          COALESCE(p.product_name, p.nc_nummer, CAST(p.id AS TEXT)),
          p.id
        """,
        (lager_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def list_stock_combined(con: sqlite3.Connection) -> list[dict]:
    """
    Combined stock overview across all lagers.
    """
    rows = con.execute(
        """
        SELECT
          p.id AS product_id,
          p.kind,
          p.nc_nummer,
          p.product_name,
          p.active,
          COALESCE(SUM(CASE WHEN s.lager_id = 1 THEN s.quantity END), 0) AS qty_konstanz,
          COALESCE(SUM(CASE WHEN s.lager_id = 2 THEN s.quantity END), 0) AS qty_sindelfingen,
          COALESCE(SUM(s.quantity), 0) AS qty_total
        FROM products p
        LEFT JOIN stock s ON s.product_id = p.id
        GROUP BY
          p.id, p.kind, p.nc_nummer, p.product_name, p.active
        ORDER BY
          p.kind,
          COALESCE(p.product_name, p.nc_nummer, CAST(p.id AS TEXT)),
          p.id
        """
    ).fetchall()
    return [dict(r) for r in rows]