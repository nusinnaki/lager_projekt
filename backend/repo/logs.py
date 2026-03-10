import sqlite3


def list_logs(con: sqlite3.Connection, limit: int = 50, offset: int = 0) -> list[dict]:
    rows = con.execute(
        """
        SELECT
          l.id,
          l.action,
          l.quantity,
          l.timestamp AS created_at,
          l.lager_id,
          g.name AS lager_name,
          l.worker_id,
          w.first_name,
          w.last_name,
          l.product_id,
          p.product_name
        FROM logs l
        JOIN lagers g ON g.id = l.lager_id
        JOIN workers w ON w.id = l.worker_id
        JOIN products p ON p.id = l.product_id
        ORDER BY l.id DESC
        LIMIT ? OFFSET ?
        """,
        (limit, offset),
    ).fetchall()
    return [dict(r) for r in rows]
