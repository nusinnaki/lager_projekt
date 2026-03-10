from fastapi import HTTPException

from backend.db import db_session
from backend.logic.sites import lager_id_from_site


def act(site: str, payload, action: str, current_user: dict) -> dict:
    lager_id = lager_id_from_site(site)
    worker_id = int(current_user["worker_id"])

    if payload.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be > 0")

    with db_session() as con:
        cur = con.cursor()

        worker = cur.execute(
            """
            SELECT active
            FROM workers
            WHERE id = ?
            """,
            (worker_id,),
        ).fetchone()

        if not worker or int(worker["active"]) != 1:
            raise HTTPException(status_code=400, detail="Invalid worker")

        product = cur.execute(
            """
            SELECT active
            FROM products
            WHERE id = ?
            """,
            (payload.product_id,),
        ).fetchone()

        if not product or int(product["active"]) != 1:
            raise HTTPException(status_code=400, detail="Invalid product")

        stock_row = cur.execute(
            """
            SELECT quantity
            FROM stock
            WHERE lager_id = ?
              AND product_id = ?
            """,
            (lager_id, payload.product_id),
        ).fetchone()

        if not stock_row:
            raise HTTPException(status_code=400, detail="Missing stock row")

        current_qty = int(stock_row["quantity"])

        if action == "load":
            new_qty = current_qty + payload.quantity
        else:
            new_qty = current_qty - payload.quantity
            if new_qty < 0:
                raise HTTPException(status_code=400, detail="Not enough stock")

        cur.execute(
            """
            UPDATE stock
            SET quantity = ?
            WHERE lager_id = ?
              AND product_id = ?
            """,
            (new_qty, lager_id, payload.product_id),
        )

        cur.execute(
            """
            INSERT INTO logs (
                action,
                lager_id,
                worker_id,
                product_id,
                quantity
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                action,
                lager_id,
                worker_id,
                payload.product_id,
                payload.quantity,
            ),
        )

    return {
        "ok": True,
        "new_quantity": new_qty,
    }
