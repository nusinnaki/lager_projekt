from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.db import db_session
from backend.logic.auth import hash_password, require_admin
from backend.logic.users import username_from_worker
from backend.models.admin import CreateUserIn, UpdateUserAdminIn, AdminResetPasswordIn
from backend.repo.products import list_categories, list_products
from backend.repo.users import list_users

router = APIRouter(prefix="/api/admin", tags=["admin"])


class CategoryCreateIn(BaseModel):
    name: str


class ProductUpdateIn(BaseModel):
    category_id: int | None = None
    threshold_red: int = 5
    threshold_yellow: int = 10
    lagerort: str | None = None
    regal: str | None = None
    fach: str | None = None
    product_name: str
    nc_nummer: str | None = None
    active: bool = True


@router.get("/users")
def admin_list_users(admin: dict = Depends(require_admin)) -> list[dict]:
    with db_session() as con:
        rows = list_users(con)
    return rows


@router.post("/users")
def admin_create_user(
    payload: CreateUserIn,
    admin: dict = Depends(require_admin),
) -> dict:
    with db_session() as con:
        worker = con.execute(
            """
            SELECT id, first_name, last_name, active
            FROM workers
            WHERE id = ?
            """,
            (payload.worker_id,),
        ).fetchone()

        if not worker:
            raise HTTPException(status_code=404, detail="Worker not found")

        if int(worker["active"]) != 1:
            raise HTTPException(status_code=400, detail="Worker inactive")

        existing_user_for_worker = con.execute(
            """
            SELECT id
            FROM users
            WHERE worker_id = ?
            """,
            (payload.worker_id,),
        ).fetchone()

        if existing_user_for_worker:
            raise HTTPException(status_code=400, detail="User already exists for this worker")

        username = username_from_worker(worker["first_name"], worker["last_name"])

        existing_username = con.execute(
            """
            SELECT id
            FROM users
            WHERE username = ?
            """,
            (username,),
        ).fetchone()

        if existing_username:
            raise HTTPException(status_code=400, detail="Generated username already exists")

        con.execute(
            """
            INSERT INTO users (
                worker_id,
                username,
                is_admin,
                is_active
            )
            VALUES (?, ?, ?, 1)
            """,
            (payload.worker_id, username, int(payload.is_admin)),
        )

    return {
        "ok": True,
        "message": "User created successfully",
        "username": username,
    }


@router.patch("/users/{user_id}/admin")
def admin_update_user_admin(
    user_id: int,
    payload: UpdateUserAdminIn,
    admin: dict = Depends(require_admin),
) -> dict:
    with db_session() as con:
        result = con.execute(
            """
            UPDATE users
            SET is_admin = ?
            WHERE id = ?
            """,
            (int(payload.is_admin), user_id),
        )

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")

    return {"ok": True, "message": "User role updated successfully"}


@router.patch("/users/{user_id}/deactivate")
def admin_deactivate_user(
    user_id: int,
    admin: dict = Depends(require_admin),
) -> dict:
    with db_session() as con:
        result = con.execute(
            """
            UPDATE users
            SET is_active = 0
            WHERE id = ?
            """,
            (user_id,),
        )

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")

    return {"ok": True, "message": "User deactivated successfully"}


@router.patch("/users/{user_id}/activate")
def admin_activate_user(
    user_id: int,
    admin: dict = Depends(require_admin),
) -> dict:
    with db_session() as con:
        result = con.execute(
            """
            UPDATE users
            SET is_active = 1
            WHERE id = ?
            """,
            (user_id,),
        )

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")

    return {"ok": True, "message": "User activated successfully"}


@router.patch("/users/{user_id}/reset-password")
def admin_reset_user_password(
    user_id: int,
    payload: AdminResetPasswordIn,
    admin: dict = Depends(require_admin),
) -> dict:
    new_hash = hash_password(payload.new_password)
    now = datetime.now(timezone.utc).isoformat()

    with db_session() as con:
        result = con.execute(
            """
            UPDATE users
            SET password_hash = ?, password_set_at = ?
            WHERE id = ?
            """,
            (new_hash, now, user_id),
        )

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")

    return {"ok": True, "message": "Password reset successfully"}


@router.get("/categories")
def admin_list_categories(admin: dict = Depends(require_admin)) -> list[dict]:
    with db_session() as con:
        return list_categories(con)


@router.post("/categories")
def admin_create_category(payload: CategoryCreateIn, admin: dict = Depends(require_admin)) -> dict:
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Category name required")

    with db_session() as con:
        try:
            con.execute(
                """
                INSERT INTO categories(name, active)
                VALUES (?, 1)
                """,
                (name,),
            )
        except Exception:
            raise HTTPException(status_code=400, detail="Category already exists")

    return {"ok": True, "message": "Category created successfully"}


@router.get("/products")
def admin_list_products(admin: dict = Depends(require_admin)) -> list[dict]:
    with db_session() as con:
        return list_products(con)


@router.patch("/products/{product_id}")
def admin_update_product(
    product_id: int,
    payload: ProductUpdateIn,
    admin: dict = Depends(require_admin),
) -> dict:
    if payload.threshold_red < 0 or payload.threshold_yellow < 0:
        raise HTTPException(status_code=400, detail="Thresholds must be >= 0")

    with db_session() as con:
        result = con.execute(
            """
            UPDATE products
            SET
              category_id = ?,
              threshold_red = ?,
              threshold_yellow = ?,
              lagerort = ?,
              regal = ?,
              fach = ?,
              product_name = ?,
              nc_nummer = ?,
              active = ?
            WHERE id = ?
            """,
            (
                payload.category_id,
                payload.threshold_red,
                payload.threshold_yellow,
                payload.lagerort,
                payload.regal,
                payload.fach,
                payload.product_name,
                payload.nc_nummer,
                int(payload.active),
                product_id,
            ),
        )

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Product not found")

    return {"ok": True, "message": "Product updated successfully"}
