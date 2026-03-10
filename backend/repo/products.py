from __future__ import annotations

import sqlite3


def list_products(con: sqlite3.Connection) -> list[dict]:
    rows = con.execute(
        """
        SELECT
          id,
          kind,
          nc_nummer,
          product_name,
          active
        FROM products
        ORDER BY id
        """
    ).fetchall()
    return [dict(r) for r in rows]