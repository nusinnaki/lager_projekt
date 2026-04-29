from __future__ import annotations

import sqlite3


def list_workers(con: sqlite3.Connection) -> list[dict]:
    rows = con.execute(
        """
        SELECT
          id,
          first_name,
          last_name,
          username,
          CASE
            WHEN password_hash IS NOT NULL AND trim(password_hash) != '' THEN 1
            ELSE 0
          END AS has_password,
          auth_provider,
          ldap_dn,
          is_admin,
          is_active,
          created_at
        FROM workers
        ORDER BY id
        """
    ).fetchall()
    return [dict(r) for r in rows]


def get_worker_by_username(con: sqlite3.Connection, username: str) -> dict | None:
    row = con.execute(
        """
        SELECT
          id,
          first_name,
          last_name,
          username,
          password_hash,
          auth_provider,
          ldap_dn,
          is_admin,
          is_active,
          created_at
        FROM workers
        WHERE username = ?
        """,
        (username,),
    ).fetchone()
    return dict(row) if row else None


def get_worker_by_id(con: sqlite3.Connection, worker_id: int) -> dict | None:
    row = con.execute(
        """
        SELECT
          id,
          first_name,
          last_name,
          username,
          password_hash,
          auth_provider,
          ldap_dn,
          is_admin,
          is_active,
          created_at
        FROM workers
        WHERE id = ?
        """,
        (worker_id,),
    ).fetchone()
    return dict(row) if row else None
