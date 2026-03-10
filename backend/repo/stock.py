import sqlite3


def list_stock_for_lager(con: sqlite3.Connection, lager_id: int) -> list[dict]:
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
        ORDER BY p.id
        """,
        (lager_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def list_stock_combined(con: sqlite3.Connection) -> list[dict]:
    rows = con.execute(
        """
        SELECT
          p.id AS product_id,
          p.product_name,
          COALESCE(MAX(CASE WHEN s.lager_id = 1 THEN s.quantity END), 0) AS qty_konstanz,
          COALESCE(MAX(CASE WHEN s.lager_id = 2 THEN s.quantity END), 0) AS qty_sindelfingen,
          COALESCE(MAX(CASE WHEN s.lager_id = 1 THEN s.quantity END), 0)
          +
          COALESCE(MAX(CASE WHEN s.lager_id = 2 THEN s.quantity END), 0) AS qty_total
        FROM products p
        LEFT JOIN stock s ON s.product_id = p.id
        WHERE p.active = 1
        GROUP BY p.id, p.product_name
        ORDER BY p.id
        """
    ).fetchall()
    return [dict(r) for r in rows]
