from __future__ import annotations

import os
from typing import Optional

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.db import init_db, db_session

app = FastAPI(title="POPSITE Lager Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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
# Helpers
# =========================================================

def lager_id_from_site(site: str) -> int:
    s = (site or "").strip().lower()
    if s == "konstanz":
        return 1
    if s == "sindelfingen":
        return 2
    raise HTTPException(status_code=400, detail="Invalid site")


def get_admin_token() -> str:
    token = (os.environ.get("ADMIN_TOKEN") or "").strip()
    if not token:
        raise RuntimeError("ADMIN_TOKEN is not set")
    return token


def require_admin(x_admin_token: Optional[str] = Header(None)) -> None:
    if (x_admin_token or "").strip() != get_admin_token():
        raise HTTPException(status_code=403, detail="Forbidden")


def admin_guard(_: None = Depends(require_admin)) -> None:
    return None


# =========================================================
# Pydantic models
# =========================================================

class ActionIn(BaseModel):
    worker_id: int
    product_id: int
    quantity: int


class NameIn(BaseModel):
    name: str


class ActiveIn(BaseModel):
    active: bool


class ProductCreateIn(BaseModel):
    kind: str
    nc_nummer: Optional[str] = None
    materialkurztext: Optional[str] = None
    product_name: Optional[str] = None


# =========================================================
# Public API
# =========================================================

@app.get("/api/{site}/workers")
def api_workers(site: str) -> list[dict]:
    lager_id_from_site(site)

    with db_session() as con:
        rows = con.execute(
            """
            SELECT
                id,
                full_name AS name,
                site,
                active
            FROM workers
            WHERE lower(site) = lower(?)
            ORDER BY COALESCE(full_name, CAST(id AS TEXT)), id
            """,
            (site,),
        ).fetchall()

        return [dict(r) for r in rows]


@app.get("/api/{site}/products")
def api_products(site: str) -> list[dict]:
    lager_id_from_site(site)

    with db_session() as con:
        rows = con.execute(
            """
            SELECT
                id,
                kind,
                nc_nummer,
                materialkurztext,
                product_name,
                active
            FROM products
            ORDER BY
                kind,
                COALESCE(materialkurztext, product_name, nc_nummer, CAST(id AS TEXT)),
                id
            """
        ).fetchall()

        return [dict(r) for r in rows]


@app.get("/api/{site}/stock")
def api_stock(site: str) -> list[dict]:
    lager_id = lager_id_from_site(site)

    with db_session() as con:
        rows = con.execute(
            """
            SELECT
                p.id AS product_id,
                p.kind,
                p.nc_nummer,
                p.materialkurztext,
                p.product_name,
                p.active,
                s.quantity
            FROM stock s
            JOIN products p ON p.id = s.product_id
            WHERE s.lager_id = ?
            ORDER BY
                p.kind,
                COALESCE(p.materialkurztext, p.product_name, p.nc_nummer, CAST(p.id AS TEXT)),
                p.id
            """,
            (lager_id,),
        ).fetchall()

        return [dict(r) for r in rows]


@app.post("/api/{site}/take")
def take(site: str, payload: ActionIn):
    return _act(site, payload, "take")


@app.post("/api/{site}/load")
def load(site: str, payload: ActionIn):
    return _act(site, payload, "load")


def _act(site: str, payload: ActionIn, action: str):
    lager_id = lager_id_from_site(site)

    if payload.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be > 0")

    with db_session() as con:
        cur = con.cursor()

        w = cur.execute(
            "SELECT active FROM workers WHERE id=?",
            (payload.worker_id,),
        ).fetchone()
        if not w or int(w["active"]) != 1:
            raise HTTPException(status_code=400, detail="Invalid worker")

        p = cur.execute(
            "SELECT active FROM products WHERE id=?",
            (payload.product_id,),
        ).fetchone()
        if not p or int(p["active"]) != 1:
            raise HTTPException(status_code=400, detail="Invalid product")

        row = cur.execute(
            "SELECT quantity FROM stock WHERE lager_id=? AND product_id=?",
            (lager_id, payload.product_id),
        ).fetchone()

        if not row:
            raise HTTPException(status_code=400, detail="Missing stock row")

        current = int(row["quantity"])

        if action == "load":
            newq = current + payload.quantity
        else:
            newq = current - payload.quantity
            if newq < 0:
                raise HTTPException(status_code=400, detail="Not enough stock")

        cur.execute(
            "UPDATE stock SET quantity=? WHERE lager_id=? AND product_id=?",
            (newq, lager_id, payload.product_id),
        )

        cur.execute(
            """
            INSERT INTO logs(action, lager_id, worker_id, product_id, quantity, note)
            VALUES (?, ?, ?, ?, ?, NULL)
            """,
            (action, lager_id, payload.worker_id, payload.product_id, payload.quantity),
        )

        con.commit()

        return {"ok": True, "new_quantity": newq}


# =========================================================
# Admin
# =========================================================

@app.get("/api/{site}/admin/ping")
def admin_ping(site: str, _: None = Depends(admin_guard)):
    lager_id_from_site(site)
    return {"ok": True}