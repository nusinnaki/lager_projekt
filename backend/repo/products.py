import sqlite3


def list_products(con: sqlite3.Connection) -> list[dict]:
    rows = con.execute(
        """
        SELECT
          p.id,
          p.category_id,
          c.name AS category_name,
          p.brand_id,
          b.name AS brand_name,
          p.product_name,
          p.nc_nummer,
          p.active
        FROM products p
        LEFT JOIN categories c ON c.id = p.category_id
        LEFT JOIN brands b ON b.id = p.brand_id
        ORDER BY p.id
        """
    ).fetchall()
    return [dict(r) for r in rows]