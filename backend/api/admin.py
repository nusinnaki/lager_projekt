from fastapi import APIRouter, Depends, HTTPException

from backend.db import db_session
from backend.logic.auth import hash_password, require_admin
from backend.models.admin import (
    WorkerCreateIn,
    WorkerUpdateIn,
    AdminResetPasswordIn,
    UpdateWorkerAdminIn,
    ProductCreateIn,
    ProductUpdateIn,
    CategoryCreateIn,
    CategoryUpdateIn,
    BrandCreateIn,
    BrandUpdateIn,
    SiteCreateIn,
    SiteUpdateIn,
    LocationCreateIn,
    LocationUpdateIn,
    ProductSiteLocationUpsertIn,
)
from backend.repo.products import list_products
from backend.repo.workers import list_workers

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/workers")
def admin_create_worker(
    payload: WorkerCreateIn,
    admin: dict = Depends(require_admin),
) -> dict:
    from backend.logic.users import username_from_worker

    first_name = payload.first_name.strip()
    last_name = payload.last_name.strip()

    if not first_name or not last_name:
        raise HTTPException(status_code=400, detail="First name and last name are required")

    username = username_from_worker(first_name, last_name)

    try:
        with db_session() as con:
            con.execute(
                """
                INSERT INTO workers(
                    first_name,
                    last_name,
                    username,
                    password_hash,
                    auth_provider,
                    ldap_dn,
                    is_admin,
                    is_active
                )
                VALUES (?, ?, ?, NULL, 'local', NULL, 0, 1)
                """,
                (first_name, last_name, username),
            )
    except Exception:
        raise HTTPException(status_code=400, detail="Worker already exists or is invalid")

    return {
        "ok": True,
        "message": "Worker created successfully",
        "username": username,
        "must_set_password": True,
    }


@router.get("/workers")
def admin_list_workers(admin: dict = Depends(require_admin)) -> list[dict]:
    with db_session() as con:
        return list_workers(con)


@router.patch("/workers/{worker_id}")
def admin_update_worker(
    worker_id: int,
    payload: WorkerUpdateIn,
    admin: dict = Depends(require_admin),
) -> dict:
    first_name = payload.first_name.strip()
    last_name = payload.last_name.strip()
    username = payload.username.strip().lower()
    auth_provider = payload.auth_provider.strip() or "local"
    ldap_dn = payload.ldap_dn.strip() if payload.ldap_dn else None

    if not first_name or not last_name:
        raise HTTPException(status_code=400, detail="First name and last name are required")

    if not username:
        raise HTTPException(status_code=400, detail="Username is required")

    with db_session() as con:
        result = con.execute(
            """
            UPDATE workers
            SET
                first_name = ?,
                last_name = ?,
                username = ?,
                auth_provider = ?,
                ldap_dn = ?,
                is_admin = ?,
                is_active = ?
            WHERE id = ?
            """,
            (
                first_name,
                last_name,
                username,
                auth_provider,
                ldap_dn,
                int(payload.is_admin),
                int(payload.is_active),
                worker_id,
            ),
        )

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Worker not found")

    return {"ok": True, "message": "Worker updated successfully"}


@router.patch("/workers/{worker_id}/admin")
def admin_update_worker_admin(
    worker_id: int,
    payload: UpdateWorkerAdminIn,
    admin: dict = Depends(require_admin),
) -> dict:
    with db_session() as con:
        result = con.execute(
            """
            UPDATE workers
            SET is_admin = ?
            WHERE id = ?
            """,
            (int(payload.is_admin), worker_id),
        )

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Worker not found")

    return {"ok": True, "message": "Worker role updated successfully"}


@router.patch("/workers/{worker_id}/deactivate")
def admin_deactivate_worker(
    worker_id: int,
    admin: dict = Depends(require_admin),
) -> dict:
    with db_session() as con:
        result = con.execute(
            """
            UPDATE workers
            SET is_active = 0
            WHERE id = ?
            """,
            (worker_id,),
        )

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Worker not found")

    return {"ok": True, "message": "Worker deactivated successfully"}


@router.patch("/workers/{worker_id}/activate")
def admin_activate_worker(
    worker_id: int,
    admin: dict = Depends(require_admin),
) -> dict:
    with db_session() as con:
        result = con.execute(
            """
            UPDATE workers
            SET is_active = 1
            WHERE id = ?
            """,
            (worker_id,),
        )

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Worker not found")

    return {"ok": True, "message": "Worker activated successfully"}


@router.patch("/workers/{worker_id}/reset-password")
def admin_reset_worker_password(
    worker_id: int,
    payload: AdminResetPasswordIn,
    admin: dict = Depends(require_admin),
) -> dict:
    with db_session() as con:
        worker = con.execute(
            "SELECT id, auth_provider FROM workers WHERE id = ?",
            (worker_id,),
        ).fetchone()

        if not worker:
            raise HTTPException(status_code=404, detail="Worker not found")

        if worker["auth_provider"] != "local":
            raise HTTPException(status_code=400, detail="This account does not use local password login")

        new_hash = hash_password(payload.new_password)

        result = con.execute(
            """
            UPDATE workers
            SET password_hash = ?
            WHERE id = ?
            """,
            (new_hash, worker_id),
        )

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Worker not found")

    return {"ok": True, "message": "Password reset successfully"}


@router.get("/products")
def admin_list_products(admin: dict = Depends(require_admin)) -> list[dict]:
    with db_session() as con:
        return list_products(con)



@router.post("/products")
def admin_create_product(
    payload: ProductCreateIn,
    admin: dict = Depends(require_admin),
) -> dict:
    name = payload.product_name.strip()
    nc = payload.nc_nummer.strip() if payload.nc_nummer else None

    if not name:
        raise HTTPException(status_code=400, detail="Product name is required")

    with db_session() as con:
        category = con.execute(
            "SELECT id FROM categories WHERE id = ?",
            (payload.category_id,),
        ).fetchone()

        if not category:
            raise HTTPException(status_code=400, detail="Category not found")

        brand = con.execute(
            "SELECT id FROM brands WHERE id = ?",
            (payload.brand_id,),
        ).fetchone()

        if not brand:
            raise HTTPException(status_code=400, detail="Brand not found")

        cur = con.execute(
            """
            INSERT INTO products(
                category_id,
                brand_id,
                product_name,
                nc_nummer,
                active
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                payload.category_id,
                payload.brand_id,
                name,
                nc,
                int(payload.active),
            ),
        )

        product_id = int(cur.lastrowid)

    return {
        "ok": True,
        "message": "Product created",
        "product_id": product_id,
    }

@router.patch("/products/{product_id}")
def admin_update_product(
    product_id: int,
    payload: ProductUpdateIn,
    admin: dict = Depends(require_admin),
) -> dict:
    name = payload.product_name.strip()
    nc = payload.nc_nummer.strip() if payload.nc_nummer else None

    if not name:
        raise HTTPException(status_code=400, detail="Product name is required")

    with db_session() as con:
        category = con.execute(
            "SELECT id FROM categories WHERE id = ?",
            (payload.category_id,),
        ).fetchone()

        if not category:
            raise HTTPException(status_code=400, detail="Category not found")

        brand = con.execute(
            "SELECT id FROM brands WHERE id = ?",
            (payload.brand_id,),
        ).fetchone()

        if not brand:
            raise HTTPException(status_code=400, detail="Brand not found")

        result = con.execute(
            """
            UPDATE products
            SET
                category_id = ?,
                brand_id = ?,
                product_name = ?,
                nc_nummer = ?,
                active = ?
            WHERE id = ?
            """,
            (
                payload.category_id,
                payload.brand_id,
                name,
                nc,
                int(payload.active),
                product_id,
            ),
        )

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Product not found")

    return {"ok": True, "message": "Product updated"}


@router.get("/categories")
def admin_list_categories(admin: dict = Depends(require_admin)) -> list[dict]:
    with db_session() as con:
        rows = con.execute(
            """
            SELECT id, name, active
            FROM categories
            ORDER BY name, id
            """
        ).fetchall()

        return [dict(r) for r in rows]


@router.post("/categories")
def admin_create_category(
    payload: CategoryCreateIn,
    admin: dict = Depends(require_admin),
) -> dict:
    name = payload.name.strip()

    if not name:
        raise HTTPException(status_code=400, detail="Category name is required")

    with db_session() as con:
        con.execute(
            """
            INSERT INTO categories(name, active)
            VALUES (?, 1)
            """,
            (name,),
        )

    return {"ok": True, "message": "Category created"}


@router.patch("/categories/{category_id}")
def admin_update_category(
    category_id: int,
    payload: CategoryUpdateIn,
    admin: dict = Depends(require_admin),
) -> dict:
    name = payload.name.strip()

    if not name:
        raise HTTPException(status_code=400, detail="Category name is required")

    with db_session() as con:
        result = con.execute(
            """
            UPDATE categories
            SET name = ?, active = ?
            WHERE id = ?
            """,
            (name, int(payload.active), category_id),
        )

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Category not found")

    return {"ok": True, "message": "Category updated"}


@router.get("/brands")
def admin_list_brands(admin: dict = Depends(require_admin)) -> list[dict]:
    with db_session() as con:
        rows = con.execute(
            """
            SELECT id, name, active
            FROM brands
            ORDER BY name, id
            """
        ).fetchall()

        return [dict(r) for r in rows]


@router.post("/brands")
def admin_create_brand(
    payload: BrandCreateIn,
    admin: dict = Depends(require_admin),
) -> dict:
    name = payload.name.strip()

    if not name:
        raise HTTPException(status_code=400, detail="Brand name is required")

    with db_session() as con:
        con.execute(
            """
            INSERT INTO brands(name, active)
            VALUES (?, 1)
            """,
            (name,),
        )

    return {"ok": True, "message": "Brand created"}


@router.patch("/brands/{brand_id}")
def admin_update_brand(
    brand_id: int,
    payload: BrandUpdateIn,
    admin: dict = Depends(require_admin),
) -> dict:
    name = payload.name.strip()

    if not name:
        raise HTTPException(status_code=400, detail="Brand name is required")

    with db_session() as con:
        result = con.execute(
            """
            UPDATE brands
            SET name = ?, active = ?
            WHERE id = ?
            """,
            (name, int(payload.active), brand_id),
        )

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Brand not found")

    return {"ok": True, "message": "Brand updated"}


@router.get("/sites")
def admin_list_sites(admin: dict = Depends(require_admin)) -> list[dict]:
    with db_session() as con:
        rows = con.execute(
            """
            SELECT id, name, active
            FROM sites
            ORDER BY name, id
            """
        ).fetchall()

        return [dict(r) for r in rows]


@router.post("/sites")
def admin_create_site(
    payload: SiteCreateIn,
    admin: dict = Depends(require_admin),
) -> dict:
    name = payload.name.strip()

    if not name:
        raise HTTPException(status_code=400, detail="Site name is required")

    with db_session() as con:
        con.execute(
            """
            INSERT INTO sites(name, active)
            VALUES (?, 1)
            """,
            (name,),
        )

    return {"ok": True, "message": "Site created"}


@router.patch("/sites/{site_id}")
def admin_update_site(
    site_id: int,
    payload: SiteUpdateIn,
    admin: dict = Depends(require_admin),
) -> dict:
    name = payload.name.strip()

    if not name:
        raise HTTPException(status_code=400, detail="Site name is required")

    with db_session() as con:
        result = con.execute(
            """
            UPDATE sites
            SET name = ?, active = ?
            WHERE id = ?
            """,
            (name, int(payload.active), site_id),
        )

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Site not found")

    return {"ok": True, "message": "Site updated"}


@router.get("/locations")
def admin_list_locations(
    site_id: int | None = None,
    admin: dict = Depends(require_admin),
) -> list[dict]:
    with db_session() as con:
        if site_id:
            rows = con.execute(
                """
                SELECT
                    l.id,
                    l.site_id,
                    s.name AS site_name,
                    l.shelf,
                    l.row,
                    l.active
                FROM locations l
                JOIN sites s ON s.id = l.site_id
                WHERE l.site_id = ?
                ORDER BY s.name, l.shelf, l.row, l.id
                """,
                (site_id,),
            ).fetchall()
        else:
            rows = con.execute(
                """
                SELECT
                    l.id,
                    l.site_id,
                    s.name AS site_name,
                    l.shelf,
                    l.row,
                    l.active
                FROM locations l
                JOIN sites s ON s.id = l.site_id
                ORDER BY s.name, l.shelf, l.row, l.id
                """
            ).fetchall()

        return [dict(r) for r in rows]


@router.post("/locations")
def admin_create_location(
    payload: LocationCreateIn,
    admin: dict = Depends(require_admin),
) -> dict:
    with db_session() as con:
        site = con.execute(
            "SELECT id FROM sites WHERE id = ?",
            (payload.site_id,),
        ).fetchone()

        if not site:
            raise HTTPException(status_code=400, detail="Site not found")

        con.execute(
            """
            INSERT OR IGNORE INTO locations(site_id, shelf, row, active)
            VALUES (?, ?, ?, ?)
            """,
            (
                payload.site_id,
                payload.shelf,
                payload.row,
                int(payload.active),
            ),
        )

    return {"ok": True, "message": "Location created"}


@router.patch("/locations/{location_id}")
def admin_update_location(
    location_id: int,
    payload: LocationUpdateIn,
    admin: dict = Depends(require_admin),
) -> dict:
    with db_session() as con:
        site = con.execute(
            "SELECT id FROM sites WHERE id = ?",
            (payload.site_id,),
        ).fetchone()

        if not site:
            raise HTTPException(status_code=400, detail="Site not found")

        result = con.execute(
            """
            UPDATE locations
            SET
                site_id = ?,
                shelf = ?,
                row = ?,
                active = ?
            WHERE id = ?
            """,
            (
                payload.site_id,
                payload.shelf,
                payload.row,
                int(payload.active),
                location_id,
            ),
        )

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Location not found")

    return {"ok": True, "message": "Location updated"}


@router.get("/product-site-locations")
def admin_list_product_site_locations(admin: dict = Depends(require_admin)) -> list[dict]:
    with db_session() as con:
        rows = con.execute(
            """
            SELECT
                psl.site_id,
                s.name AS site_name,
                psl.product_id,
                p.product_name,
                psl.location_id,
                l.shelf,
                l.row
            FROM product_site_locations psl
            JOIN sites s ON s.id = psl.site_id
            JOIN products p ON p.id = psl.product_id
            JOIN locations l ON l.id = psl.location_id
            ORDER BY p.product_name, s.name
            """
        ).fetchall()

        return [dict(r) for r in rows]


@router.put("/products/{product_id}/default-location")
def admin_set_default_product_location(
    product_id: int,
    payload: ProductSiteLocationUpsertIn,
    admin: dict = Depends(require_admin),
) -> dict:
    with db_session() as con:
        product = con.execute(
            "SELECT id, active FROM products WHERE id = ?",
            (product_id,),
        ).fetchone()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        site = con.execute(
            "SELECT id, active FROM sites WHERE id = ?",
            (payload.site_id,),
        ).fetchone()

        if not site:
            raise HTTPException(status_code=404, detail="Site not found")

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

        if int(location["site_id"]) != int(payload.site_id):
            raise HTTPException(status_code=400, detail="Location does not belong to selected site")

        if int(location["active"]) != 1:
            raise HTTPException(status_code=400, detail="Location is inactive")

        con.execute(
            """
            INSERT INTO product_site_locations(site_id, product_id, location_id)
            VALUES (?, ?, ?)
            ON CONFLICT(site_id, product_id)
            DO UPDATE SET location_id = excluded.location_id
            """,
            (
                payload.site_id,
                product_id,
                payload.location_id,
            ),
        )

    return {"ok": True, "message": "Default product location updated"}