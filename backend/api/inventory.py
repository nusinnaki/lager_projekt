from fastapi import APIRouter, Depends, HTTPException

from backend.db import db_session
from backend.logic.auth import get_current_user
from backend.logic.sites import lager_id_from_site
from backend.logic.stock import act
from backend.models.inventory import ActionIn
from backend.repo.logs import list_logs
from backend.repo.products import list_products
from backend.repo.stock import list_stock_combined, list_stock_for_lager
from backend.repo.workers import list_workers

router = APIRouter(prefix="/api", tags=["inventory"])


@router.get("/resolve")
def resolve(code: str, current_user: dict = Depends(get_current_user)) -> dict:
    try:
        lager_id_str, product_id_str = code.split("-")
        lager_id = int(lager_id_str)
        product_id = int(product_id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid QR format")

    with db_session() as con:
        product = con.execute(
            """
            SELECT
                id,
                product_name,
                nc_nummer
            FROM products
            WHERE id = ?
            """,
            (product_id,),
        ).fetchone()

        if not product:
            raise HTTPException(status_code=404, detail="Unknown product")

        stock_row = con.execute(
            """
            SELECT quantity
            FROM stock
            WHERE lager_id = ?
              AND product_id = ?
            """,
            (lager_id, product_id),
        ).fetchone()

        qty = int(stock_row["quantity"]) if stock_row else 0

    return {
        "lager_id": lager_id,
        "product_id": product_id,
        "product_name": product["product_name"],
        "nc_nummer": product["nc_nummer"],
        "quantity": qty,
    }


@router.get("/logs")
def api_logs(
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    if limit < 1:
        limit = 1
    if limit > 200:
        limit = 200
    if offset < 0:
        offset = 0

    with db_session() as con:
        return list_logs(con, limit=limit, offset=offset)


@router.get("/stock/combined")
def api_stock_combined(current_user: dict = Depends(get_current_user)) -> list[dict]:
    with db_session() as con:
        return list_stock_combined(con)


@router.get("/{site}/workers")
def api_workers(site: str, current_user: dict = Depends(get_current_user)) -> list[dict]:
    lager_id_from_site(site)

    with db_session() as con:
        return list_workers(con)


@router.get("/{site}/products")
def api_products(site: str, current_user: dict = Depends(get_current_user)) -> list[dict]:
    lager_id_from_site(site)

    with db_session() as con:
        return list_products(con)


@router.get("/{site}/stock")
def api_stock(site: str, current_user: dict = Depends(get_current_user)) -> list[dict]:
    lager_id = lager_id_from_site(site)

    with db_session() as con:
        return list_stock_for_lager(con, lager_id)


@router.post("/{site}/take")
def take(
    site: str,
    payload: ActionIn,
    current_user: dict = Depends(get_current_user),
) -> dict:
    return act(site, payload, "take", current_user)


@router.post("/{site}/load")
def load(
    site: str,
    payload: ActionIn,
    current_user: dict = Depends(get_current_user),
) -> dict:
    return act(site, payload, "load", current_user)
