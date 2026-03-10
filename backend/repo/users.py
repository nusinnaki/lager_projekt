from __future__ import annotations

import sqlite3


def get_user_by_username(con: sqlite3.Connection, username: str) -> dict | None:
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
        ORDER BY w.last_name, w.first_name, u.id
        """
    ).fetchall()
    return [dict(r) for r in rows]