from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.db import db_session
from backend.repo.workers import get_worker_by_id

SECRET_KEY = "replace-this-with-a-long-random-secret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 8 * 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def create_access_token(worker_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(worker_id),
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def serialize_worker(worker: dict) -> dict:
    return {
        "id": worker["id"],
        "username": worker["username"],
        "first_name": worker["first_name"],
        "last_name": worker["last_name"],
        "auth_provider": worker["auth_provider"],
        "ldap_dn": worker["ldap_dn"],
        "is_admin": bool(worker["is_admin"]),
        "is_active": bool(worker["is_active"]),
        "created_at": worker["created_at"],
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
        worker_id = int(sub)
    except (JWTError, ValueError):
        raise credentials_exception

    with db_session() as con:
        worker = get_worker_by_id(con, worker_id)

    if not worker:
        raise credentials_exception

    if int(worker["is_active"]) != 1:
        raise HTTPException(status_code=403, detail="Account inactive")

    return worker


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if int(current_user["is_admin"]) != 1:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user