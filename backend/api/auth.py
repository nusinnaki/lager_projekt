from fastapi import APIRouter, Depends, HTTPException

from backend.db import db_session
from backend.logic.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    serialize_worker,
    verify_password,
)
from backend.models.auth import ChangePasswordIn, LoginIn, LoginOut, SetPasswordIn
from backend.repo.workers import get_worker_by_username

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/set-password")
def set_password(payload: SetPasswordIn) -> dict:
    with db_session() as con:
        worker = get_worker_by_username(con, payload.username)

        if not worker:
            raise HTTPException(status_code=404, detail="Worker not found")

        if int(worker["is_active"]) != 1:
            raise HTTPException(status_code=403, detail="Account inactive")

        if worker["auth_provider"] != "local":
            raise HTTPException(status_code=400, detail="This account does not use local password login")

        if worker["password_hash"] is not None:
            raise HTTPException(status_code=400, detail="Password already set")

        password_hash = hash_password(payload.password)

        con.execute(
            """
            UPDATE workers
            SET password_hash = ?
            WHERE id = ?
            """,
            (password_hash, worker["id"]),
        )

    return {"ok": True, "message": "Password set successfully"}


@router.post("/login", response_model=LoginOut)
def login(payload: LoginIn) -> dict:
    with db_session() as con:
        worker = get_worker_by_username(con, payload.username)

    if not worker:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if int(worker["is_active"]) != 1:
        raise HTTPException(status_code=403, detail="Account inactive")

    if worker["auth_provider"] != "local":
        raise HTTPException(status_code=400, detail="This account does not use local password login")

    if worker["password_hash"] is None:
        raise HTTPException(status_code=400, detail="Password not set yet")

    if not verify_password(payload.password, worker["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token(worker["id"])

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": serialize_worker(worker),
    }


@router.get("/me")
def auth_me(current_user: dict = Depends(get_current_user)) -> dict:
    return serialize_worker(current_user)


@router.post("/change-password")
def change_password(
    payload: ChangePasswordIn,
    current_user: dict = Depends(get_current_user),
) -> dict:
    if current_user["auth_provider"] != "local":
        raise HTTPException(status_code=400, detail="This account does not use local password login")

    if current_user["password_hash"] is None:
        raise HTTPException(status_code=400, detail="Password not set yet")

    if not verify_password(payload.current_password, current_user["password_hash"]):
        raise HTTPException(status_code=401, detail="Current password is incorrect")

    new_hash = hash_password(payload.new_password)

    with db_session() as con:
        con.execute(
            """
            UPDATE workers
            SET password_hash = ?
            WHERE id = ?
            """,
            (new_hash, current_user["id"]),
        )

    return {"ok": True, "message": "Password changed successfully"}