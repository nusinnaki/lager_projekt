from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field

from backend.db import (
    db_session,
    get_user_by_id,
    get_user_by_username,
    init_db,
    lager_id_from_site,
    list_products,
    list_stock_combined,
    list_stock_for_lager,
    list_users,
    list_workers,
    username_from_worker,
)

app = FastAPI(title="POPSITE Lager Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = "replace-this-with-a-long-random-secret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 8 * 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# =========================================================
# Startup
# =========================================================

@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


# =========================================================
# Password / Token helpers
# =========================================================

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def serialize_user(user: dict) -> dict:
    return {
        "id": user["id"],
        "worker_id": user["worker_id"],
        "username": user["username"],
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "is_admin": bool(user["is_admin"]),
        "is_active": bool(user["is_active"]),
        "password_set_at": user["password_set_at"],
        "created_at": user["created_at"],
    }


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if sub is None:
            raise credentials_exception
        user_id = int(sub)
    except (JWTError, ValueError):
        raise credentials_exception

    with db_session() as con:
        user = get_user_by_id(con, user_id)

    if not user:
        raise credentials_exception

    if int(user["is_active"]) != 1:
        raise HTTPException(status_code=403, detail="Account inactive")

    return user


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if int(current_user["is_admin"]) != 1:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


# =========================================================
# Models
# =========================================================

class ActionIn(BaseModel):
    product_id: int
    quantity: int


class ProductCreateIn(BaseModel):
    kind: str
    nc_nummer: Optional[str] = None
    product_name: str


class SetPasswordIn(BaseModel):
    username: str
    password: str = Field(min_length=8)


class LoginIn(BaseModel):
    username: str
    password: str


class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class CreateUserIn(BaseModel):
    worker_id: int
    is_admin: bool = False


class UpdateUserAdminIn(BaseModel):
    is_admin: bool


class LoginOut(BaseModel):
    access_token: str
    token_type: str
    user: dict


# =========================================================
# Auth API
# =========================================================

@app.post("/api/auth/set-password")
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


@app.post("/api/auth/login", response_model=LoginOut)
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


@app.get("/api/auth/me")
def auth_me(current_user: dict = Depends(get_current_user)) -> dict:
    return serialize_user(current_user)


@app.post("/api/auth/change-password")
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


# =========================================================
# Admin user management
# =========================================================

@app.get("/api/admin/users")
def admin_list_users(admin: dict = Depends(require_admin)) -> list[dict]:
    with db_session() as con:
        rows = list_users(con)
    return rows


@app.post("/api/admin/users")
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


@app.patch("/api/admin/users/{user_id}/admin")
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


@app.patch("/api/admin/users/{user_id}/deactivate")
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


@app.patch("/api/admin/users/{user_id}/activate")
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


# =========================================================
# QR resolve
# =========================================================

@app.get("/api/resolve")
def resolve(code: str) -> dict:
    """
    QR format:
        1-3  -> lager_id=1, product_id=3
        2-8  -> lager_id=2, product_id=8
    """
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


# =========================================================
# Public / authenticated inventory API
# =========================================================

@app.get("/api/{site}/workers")
def api_workers(site: str, current_user: dict = Depends(get_current_user)) -> list[dict]:
    lager_id_from_site(site)

    with db_session() as con:
        return list_workers(con)


@app.get("/api/{site}/products")
def api_products(site: str, current_user: dict = Depends(get_current_user)) -> list[dict]:
    lager_id_from_site(site)

    with db_session() as con:
        return list_products(con)


@app.get("/api/{site}/stock")
def api_stock(site: str, current_user: dict = Depends(get_current_user)) -> list[dict]:
    lager_id = lager_id_from_site(site)

    with db_session() as con:
        return list_stock_for_lager(con, lager_id)


@app.get("/api/stock/combined")
def api_stock_all(current_user: dict = Depends(get_current_user)) -> list[dict]:
    with db_session() as con:
        return list_stock_combined(con)


@app.post("/api/{site}/take")
def take(
    site: str,
    payload: ActionIn,
    current_user: dict = Depends(get_current_user),
) -> dict:
    return _act(site, payload, "take", current_user)


@app.post("/api/{site}/load")
def load(
    site: str,
    payload: ActionIn,
    current_user: dict = Depends(get_current_user),
) -> dict:
    return _act(site, payload, "load", current_user)


# =========================================================
# Core action logic
# =========================================================

def _act(site: str, payload: ActionIn, action: str, current_user: dict) -> dict:
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