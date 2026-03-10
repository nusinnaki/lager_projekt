from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from backend.db import db_session
from backend.logic.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    serialize_user,
    verify_password,
)
from backend.models.auth import ChangePasswordIn, LoginIn, LoginOut, SetPasswordIn
from backend.repo.users import get_user_by_username

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/set-password")
def set_password(payload: SetPasswordIn) -> dict:
    with db_session() as con:
        user = get_user_by_username(con, payload.username)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if int(user["is_active"]) != 1:
            raise HTTPException(status_code=403, detail="Account inactive")

        if user["password_hash"] is not None:
            raise HTTPException(status_code=400, detail="Password already set")

        password_hash = hash_password(payload.password)
        now = datetime.now(timezone.utc).isoformat()

        con.execute(
            """
            UPDATE users
            SET password_hash = ?, password_set_at = ?
            WHERE id = ?
            """,
            (password_hash, now, user["id"]),
        )

    return {"ok": True, "message": "Password set successfully"}


@router.post("/login", response_model=LoginOut)
def login(payload: LoginIn) -> dict:
    with db_session() as con:
        user = get_user_by_username(con, payload.username)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if int(user["is_active"]) != 1:
        raise HTTPException(status_code=403, detail="Account inactive")

    if user["password_hash"] is None:
        raise HTTPException(status_code=400, detail="Password not set yet")

    if not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token(user["id"])

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": serialize_user(user),
    }


@router.get("/me")
def auth_me(current_user: dict = Depends(get_current_user)) -> dict:
    return serialize_user(current_user)


@router.post("/change-password")
def change_password(
    payload: ChangePasswordIn,
    current_user: dict = Depends(get_current_user),
) -> dict:
    if current_user["password_hash"] is None:
        raise HTTPException(status_code=400, detail="Password not set yet")

    if not verify_password(payload.current_password, current_user["password_hash"]):
        raise HTTPException(status_code=401, detail="Current password is incorrect")

    new_hash = hash_password(payload.new_password)
    now = datetime.now(timezone.utc).isoformat()

    with db_session() as con:
        con.execute(
            """
            UPDATE users
            SET password_hash = ?, password_set_at = ?
            WHERE id = ?
            """,
            (new_hash, now, current_user["id"]),
        )

    return {"ok": True, "message": "Password changed successfully"}
