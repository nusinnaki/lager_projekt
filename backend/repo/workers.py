from __future__ import annotations

import sqlite3


def list_workers(con: sqlite3.Connection) -> list[dict]:
    rows = con.execute(
        """
        SELECT
          id,
          first_name,
          last_name,
          first_name || ' ' || last_name AS name,
          active
        FROM workers
        ORDER BY last_name, first_name, id
        """
    ).fetchall()
    return [dict(r) for r in rows]