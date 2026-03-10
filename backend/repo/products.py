import sqlite3


def list_products(con: sqlite3.Connection) -> list[dict]:
    rows = con.execute(
        """
        SELECT
          p.id,
          p.kind,
          p.nc_nummer,
          p.product_name,
          p.active,
          p.category_id,
          c.name AS category_name,
          p.threshold_red,
          p.threshold_yellow,
          p.lagerort,
          p.regal,
          p.fach
        FROM products p
        LEFT JOIN categories c ON c.id = p.category_id
        ORDER BY p.id
        """
    ).fetchall()
    return [dict(r) for r in rows]


def list_categories(con: sqlite3.Connection) -> list[dict]:
    rows = con.execute(
        """
        SELECT id, name, active
        FROM categories
        ORDER BY name
        """
    ).fetchall()
    return [dict(r) for r in rows]
