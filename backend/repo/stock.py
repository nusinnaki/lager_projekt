import sqlite3


def list_stock_for_site(con: sqlite3.Connection, site_id: int) -> list[dict]:
    rows = con.execute(
        """
        SELECT
          p.id AS product_id,
          p.product_name,
          p.nc_nummer,
          p.category_id,
          c.name AS category_name,
          p.brand_id,
          b.name AS brand_name,
          psl.location_id,
          loc.site_id,
          st.name AS site_name,
          loc.shelf,
          loc.row,
          COALESCE(s.quantity, 0) AS quantity
        FROM products p
        LEFT JOIN categories c ON c.id = p.category_id
        LEFT JOIN brands b ON b.id = p.brand_id
        JOIN sites st ON st.id = ?
        LEFT JOIN product_site_locations psl
          ON psl.product_id = p.id
         AND psl.site_id = st.id
        LEFT JOIN locations loc
          ON loc.id = psl.location_id
         AND loc.site_id = st.id
         AND loc.active = 1
        LEFT JOIN stock s
          ON s.product_id = p.id
         AND s.location_id = loc.id
        WHERE p.active = 1
          AND st.active = 1
        ORDER BY p.id, loc.shelf, loc.row, loc.id
        """,
        (site_id,),
    ).fetchall()

    return [dict(r) for r in rows]


def list_stock_combined(con: sqlite3.Connection) -> list[dict]:
    rows = con.execute(
        """
        SELECT
          p.id AS product_id,
          p.product_name,
          p.nc_nummer,
          p.category_id,
          c.name AS category_name,
          p.brand_id,
          b.name AS brand_name,
          psl.location_id,
          st.id AS site_id,
          st.name AS site_name,
          loc.shelf,
          loc.row,
          COALESCE(s.quantity, 0) AS quantity
        FROM products p
        CROSS JOIN sites st
        LEFT JOIN categories c ON c.id = p.category_id
        LEFT JOIN brands b ON b.id = p.brand_id
        LEFT JOIN product_site_locations psl
          ON psl.product_id = p.id
         AND psl.site_id = st.id
        LEFT JOIN locations loc
          ON loc.id = psl.location_id
         AND loc.site_id = st.id
         AND loc.active = 1
        LEFT JOIN stock s
          ON s.product_id = p.id
         AND s.location_id = loc.id
        WHERE p.active = 1
          AND st.active = 1
        ORDER BY p.id, st.name, loc.shelf, loc.row, loc.id
        """
    ).fetchall()

    return [dict(r) for r in rows]