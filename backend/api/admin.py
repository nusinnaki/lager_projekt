from fastapi import APIRouter, Depends, HTTPException

from backend.db import db_session
from backend.logic.auth import require_admin
from backend.logic.users import username_from_worker
from backend.models.admin import CreateUserIn, UpdateUserAdminIn
from backend.repo.users import list_users

router = APIRouter(prefix="/api/admin", tags=["admin"])


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
