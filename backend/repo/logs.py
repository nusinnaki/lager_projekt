import sqlite3


def list_logs(con: sqlite3.Connection, limit: int = 50, offset: int = 0) -> list[dict]:
    rows = con.execute(
        """
        SELECT
          l.id,
          l.action,
          l.quantity,
          l.timestamp AS created_at,
          l.location_id,
          loc.site_id,
          s.name AS site_name,
          loc.shelf,
          loc.row,
          l.worker_id,
          w.first_name,
          w.last_name,
          w.username,
          l.product_id,
          p.product_name,
          p.nc_nummer,
          c.name AS category_name,
          b.name AS brand_name
        FROM logs l
        JOIN locations loc ON loc.id = l.location_id
        JOIN sites s ON s.id = loc.site_id
        JOIN workers w ON w.id = l.worker_id
        JOIN products p ON p.id = l.product_id
        LEFT JOIN categories c ON c.id = p.category_id
        LEFT JOIN brands b ON b.id = p.brand_id
        ORDER BY l.id DESC
        LIMIT ? OFFSET ?
        """,
        (limit, offset),
    ).fetchall()

    return [dict(r) for r in rows]