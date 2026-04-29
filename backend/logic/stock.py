from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import HTTPException

from backend.db import db_session
from backend.logic.sites import site_id_from_name


def get_default_location(con, site_id: int, product_id: int) -> int:
    row = con.execute(
        """
        SELECT
          psl.location_id,
          l.site_id,
          l.active
        FROM product_site_locations psl
        JOIN locations l ON l.id = psl.location_id
        WHERE psl.site_id = ?
          AND psl.product_id = ?
        """,
        (site_id, product_id),
    ).fetchone()

    if not row:
        raise HTTPException(
            status_code=400,
            detail="No default location defined for this product at this site",
        )

    if int(row["site_id"]) != int(site_id):
        raise HTTPException(
            status_code=400,
            detail="Mapped location does not belong to this site",
        )

    if int(row["active"]) != 1:
        raise HTTPException(
            status_code=400,
            detail="Mapped location is inactive",
        )

    return int(row["location_id"])


def act(site_name, payload, action, current_user):
    if action not in {"load", "take"}:
        raise HTTPException(status_code=400, detail="Invalid action")

    if int(payload.quantity) <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than 0")

    with db_session() as con:
        site_id = site_id_from_name(con, site_name)

        product = con.execute(
            """
            SELECT id, active
            FROM products
            WHERE id = ?
            """,
            (payload.product_id,),
        ).fetchone()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        if int(product["active"]) != 1:
            raise HTTPException(status_code=400, detail="Product is inactive")

        location_id = get_default_location(con, site_id, payload.product_id)

        row = con.execute(
            """
            SELECT quantity
            FROM stock
            WHERE location_id = ?
              AND product_id = ?
            """,
            (location_id, payload.product_id),
        ).fetchone()

        current_quantity = int(row["quantity"]) if row else 0

        if action == "take":
            if current_quantity < payload.quantity:
                raise HTTPException(status_code=400, detail="Not enough stock")
            new_quantity = current_quantity - payload.quantity
        else:
            new_quantity = current_quantity + payload.quantity

        con.execute(
            """
            INSERT INTO stock(location_id, product_id, quantity)
            VALUES (?, ?, ?)
            ON CONFLICT(location_id, product_id)
            DO UPDATE SET quantity = excluded.quantity
            """,
            (location_id, payload.product_id, new_quantity),
        )

        timestamp = datetime.now(ZoneInfo("Europe/Berlin")).strftime("%Y-%m-%d %H:%M:%S")

        con.execute(
            """
            INSERT INTO logs(action, location_id, worker_id, product_id, quantity, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                action,
                location_id,
                current_user["id"],
                payload.product_id,
                payload.quantity,
                timestamp,
            ),
        )

    return {
        "status": "ok",
        "location_id": location_id,
        "new_quantity": new_quantity,
    }