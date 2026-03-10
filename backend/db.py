from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db" / "Lager_live.db"
SCHEMA_PATH = ROOT / "backend" / "schema.sql"


class DbConfigError(RuntimeError):
    pass


class DbConnectionError(RuntimeError):
    pass


class DbSchemaError(RuntimeError):
    pass


@dataclass(frozen=True)
class DbConfig:
    db_path: Path = DB_PATH
    schema_path: Path = SCHEMA_PATH


def get_conn(cfg: DbConfig = DbConfig()) -> sqlite3.Connection:
    db_dir = cfg.db_path.parent

    if not db_dir.exists():
        raise DbConfigError(f"DB directory not found: {db_dir}")

    if cfg.db_path.exists() and not cfg.db_path.is_file():
        raise DbConfigError(f"DB path is not a file: {cfg.db_path}")

    try:
        con = sqlite3.connect(str(cfg.db_path), timeout=10)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON;")
        con.execute("PRAGMA journal_mode = WAL;")
        con.execute("PRAGMA synchronous = NORMAL;")
        return con
    except sqlite3.Error as e:
        raise DbConnectionError(f"Cannot open sqlite DB: {cfg.db_path}") from e


@contextmanager
def db_session(cfg: DbConfig = DbConfig()) -> Iterator[sqlite3.Connection]:
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
    if not cfg.schema_path.exists():
        raise DbSchemaError(f"schema.sql missing: {cfg.schema_path}")

    try:
        sql = cfg.schema_path.read_text(encoding="utf-8").strip()
    except OSError as e:
        raise DbSchemaError(f"Cannot read schema.sql: {cfg.schema_path}") from e

    if not sql:
        raise DbSchemaError(f"schema.sql is empty: {cfg.schema_path}")

    with db_session(cfg) as con:
        try:
            con.executescript(sql)
        except sqlite3.Error as e:
            raise DbSchemaError("Failed to apply schema.sql") from e
