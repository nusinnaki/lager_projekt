from fastapi import APIRouter, Depends, HTTPException

from backend.db import db_session
from backend.logic.auth import get_current_user
from backend.logic.sites import site_id_from_name
from backend.logic.stock import act
from backend.models.inventory import ActionIn, ProductLocationIn
from backend.repo.logs import list_logs
from backend.repo.products import list_products
from backend.repo.stock import list_stock_combined, list_stock_for_site
from backend.repo.workers import list_workers

router = APIRouter(prefix="/api", tags=["inventory"])


@router.get("/resolve")
def resolve(code: str, current_user: dict = Depends(get_current_user)) -> dict:
    try:
        site_id_str, product_id_str = code.split("-")
        site_id = int(site_id_str)
        product_id = int(product_id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid QR format")

    with db_session() as con:
        site = con.execute(
            """
            SELECT id, name
            FROM sites
            WHERE id = ?
              AND active = 1
            """,
            (site_id,),
        ).fetchone()

        if not site:
            raise HTTPException(status_code=404, detail="Unknown site")

        product = con.execute(
            """
            SELECT
              p.id,
              p.product_name,
              p.nc_nummer,
              p.category_id,
              c.name AS category_name,
              p.brand_id,
              b.name AS brand_name
            FROM products p
            LEFT JOIN categories c ON c.id = p.category_id
            LEFT JOIN brands b ON b.id = p.brand_id
            WHERE p.id = ?
              AND p.active = 1
            """,
            (product_id,),
        ).fetchone()

        if not product:
            raise HTTPException(status_code=404, detail="Unknown product")

        location = con.execute(
            """
            SELECT
              l.id AS location_id,
              l.shelf,
              l.row
            FROM product_site_locations psl
            JOIN locations l ON l.id = psl.location_id
            WHERE psl.site_id = ?
              AND psl.product_id = ?
              AND l.active = 1
            """,
            (site_id, product_id),
        ).fetchone()

        if location:
            location_id = location["location_id"]
            shelf = location["shelf"]
            row = location["row"]
        else:
            location_id = None
            shelf = None
            row = None

        quantity = 0

        if location_id is not None:
            stock_row = con.execute(
                """
                SELECT quantity
                FROM stock
                WHERE location_id = ?
                  AND product_id = ?
                """,
                (location_id, product_id),
            ).fetchone()

            if stock_row:
                quantity = int(stock_row["quantity"])

    return {
        "site_id": site["id"],
        "site_name": site["name"],
        "product_id": product["id"],
        "product_name": product["product_name"],
        "nc_nummer": product["nc_nummer"],
        "category_id": product["category_id"],
        "category_name": product["category_name"],
        "brand_id": product["brand_id"],
        "brand_name": product["brand_name"],
        "location_id": location_id,
        "shelf": shelf,
        "row": row,
        "quantity": quantity,
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


@router.get("/{site}/products/{product_id}/resolve")
def api_resolve_product_for_site(
    site: str,
    product_id: int,
    current_user: dict = Depends(get_current_user),
) -> dict:
    with db_session() as con:
        site_id = site_id_from_name(con, site)

        product = con.execute(
            """
            SELECT
              p.id,
              p.product_name,
              p.nc_nummer,
              p.category_id,
              c.name AS category_name,
              p.brand_id,
              b.name AS brand_name
            FROM products p
            LEFT JOIN categories c ON c.id = p.category_id
            LEFT JOIN brands b ON b.id = p.brand_id
            WHERE p.id = ?
              AND p.active = 1
            """,
            (product_id,),
        ).fetchone()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        location = con.execute(
            """
            SELECT
              l.id AS location_id,
              l.shelf,
              l.row
            FROM product_site_locations psl
            JOIN locations l ON l.id = psl.location_id
            WHERE psl.site_id = ?
              AND psl.product_id = ?
              AND l.active = 1
            """,
            (site_id, product_id),
        ).fetchone()

        location_id = location["location_id"] if location else None
        shelf = location["shelf"] if location else None
        row = location["row"] if location else None

        quantity = 0

        if location_id is not None:
            stock_row = con.execute(
                """
                SELECT quantity
                FROM stock
                WHERE location_id = ?
                  AND product_id = ?
                """,
                (location_id, product_id),
            ).fetchone()

            if stock_row:
                quantity = int(stock_row["quantity"])

    return {
        "site_id": site_id,
        "site_name": site,
        "product_id": product["id"],
        "product_name": product["product_name"],
        "nc_nummer": product["nc_nummer"],
        "category_id": product["category_id"],
        "category_name": product["category_name"],
        "brand_id": product["brand_id"],
        "brand_name": product["brand_name"],
        "location_id": location_id,
        "shelf": shelf,
        "row": row,
        "quantity": quantity,
    }


@router.get("/{site}/workers")
def api_workers(site: str, current_user: dict = Depends(get_current_user)) -> list[dict]:
    with db_session() as con:
        site_id_from_name(con, site)
        return list_workers(con)


@router.get("/{site}/products")
def api_products(site: str, current_user: dict = Depends(get_current_user)) -> list[dict]:
    with db_session() as con:
        site_id_from_name(con, site)
        return list_products(con)


@router.get("/{site}/stock")
def api_stock(site: str, current_user: dict = Depends(get_current_user)) -> list[dict]:
    with db_session() as con:
        site_id = site_id_from_name(con, site)
        return list_stock_for_site(con, site_id)


@router.get("/{site}/locations")
def api_locations(
    site: str,
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    with db_session() as con:
        site_id = site_id_from_name(con, site)

        rows = con.execute(
            """
            SELECT
              id,
              site_id,
              shelf,
              row,
              active
            FROM locations
            WHERE site_id = ?
              AND active = 1
            ORDER BY shelf, row, id
            """,
            (site_id,),
        ).fetchall()

        return [dict(r) for r in rows]


@router.patch("/{site}/products/{product_id}/location")
def api_set_product_location(
    site: str,
    product_id: int,
    payload: ProductLocationIn,
    current_user: dict = Depends(get_current_user),
) -> dict:
    with db_session() as con:
        site_id = site_id_from_name(con, site)

        product = con.execute(
            """
            SELECT id, active
            FROM products
            WHERE id = ?
            """,
            (product_id,),
        ).fetchone()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        if int(product["active"]) != 1:
            raise HTTPException(status_code=400, detail="Product is inactive")

        location = con.execute(
            """
            SELECT id, site_id, active
            FROM locations
            WHERE id = ?
            """,
            (payload.location_id,),
        ).fetchone()

        if not location:
            raise HTTPException(status_code=404, detail="Location not found")

        if int(location["active"]) != 1:
            raise HTTPException(status_code=400, detail="Location is inactive")

        if int(location["site_id"]) != int(site_id):
            raise HTTPException(
                status_code=400,
                detail="Location does not belong to this site",
            )

        con.execute(
            """
            INSERT INTO product_site_locations(site_id, product_id, location_id)
            VALUES (?, ?, ?)
            ON CONFLICT(site_id, product_id)
            DO UPDATE SET location_id = excluded.location_id
            """,
            (site_id, product_id, payload.location_id),
        )

    return {"ok": True, "message": "Product location updated"}


@router.delete("/{site}/products/{product_id}/location")
def api_remove_product_location(
    site: str,
    product_id: int,
    current_user: dict = Depends(get_current_user),
) -> dict:
    with db_session() as con:
        site_id = site_id_from_name(con, site)

        con.execute(
            """
            DELETE FROM product_site_locations
            WHERE site_id = ?
              AND product_id = ?
            """,
            (site_id, product_id),
        )

    return {"ok": True, "message": "Product location removed"}


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