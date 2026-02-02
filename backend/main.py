import os
from typing import Optional

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.db import get_conn, lager_id_from_site

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def require_admin(token: Optional[str]) -> None:
    if token != os.environ.get("ADMIN_TOKEN"):
        raise HTTPException(403, "Forbidden")

class ActionIn(BaseModel):
    worker_id: int
    product_id: int
    quantity: int

class NameIn(BaseModel):
    name: str

class ActiveIn(BaseModel):
    active: bool

class ProductCreateIn(BaseModel):
    kind: str  # "netcom" or "werkzeug"
    nc_nummer: Optional[str] = None
    materialkurztext: Optional[str] = None
    product_name: Optional[str] = None

# ---------- PUBLIC ----------

@app.get("/api/{site}/workers")
def workers(site: str):
    _ = lager_id_from_site(site)
    con = get_conn()
    try:
        rows = con.execute("SELECT id, name, active FROM workers ORDER BY name").fetchall()
        return [dict(r) for r in rows]
    finally:
        con.close()

@app.get("/api/{site}/products")
def products(site: str):
    _ = lager_id_from_site(site)
    con = get_conn()
    try:
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
              COALESCE(materialkurztext, product_name, nc_nummer, id)
            """
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        con.close()


@app.get("/api/{site}/stock")
def stock(site: str):
    lager_id = lager_id_from_site(site)
    con = get_conn()
    try:
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
              COALESCE(p.materialkurztext, p.product_name, p.nc_nummer, p.id)
            """,
            (lager_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        con.close()


@app.get("/api/{site}/products/lookup/{qr}")
def product_lookup(site: str, qr: int):
    _ = lager_id_from_site(site)
    con = get_conn()
    try:
        row = con.execute(
            """
            SELECT
              id,
              kind,
              nc_nummer,
              materialkurztext,
              product_name,
              active
            FROM products
            WHERE id = ?
            """,
            (qr,),
        ).fetchone()
        if not row:
            raise HTTPException(404, "Unknown QR")
        if int(row["active"]) != 1:
            raise HTTPException(400, "Inactive product")
        return dict(row)
    finally:
        con.close()


@app.post("/api/{site}/take")
def take(site: str, payload: ActionIn):
    return _act(site, payload, "take")

@app.post("/api/{site}/load")
def load(site: str, payload: ActionIn):
    return _act(site, payload, "load")

def _act(site: str, payload: ActionIn, action: str):
    lager_id = lager_id_from_site(site)

    if payload.quantity <= 0:
        raise HTTPException(400, "Quantity must be > 0")

    con = get_conn()
    try:
        cur = con.cursor()

        w = cur.execute("SELECT active FROM workers WHERE id=?", (payload.worker_id,)).fetchone()
        if not w or int(w["active"]) != 1:
            raise HTTPException(400, "Invalid worker")

        p = cur.execute("SELECT active FROM products WHERE id=?", (payload.product_id,)).fetchone()
        if not p or int(p["active"]) != 1:
            raise HTTPException(400, "Invalid product")

        row = cur.execute(
            "SELECT quantity FROM stock WHERE lager_id=? AND product_id=?",
            (lager_id, payload.product_id),
        ).fetchone()
        if not row:
            raise HTTPException(400, "Missing stock row")

        current = int(row["quantity"])
        if action == "load":
            newq = current + payload.quantity
        else:
            newq = current - payload.quantity
            if newq < 0:
                raise HTTPException(400, "Not enough stock")

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
    finally:
        con.close()

# ---------- ADMIN ----------

@app.get("/api/{site}/admin/ping")
def admin_ping(site: str, x_admin_token: Optional[str] = Header(None)):
    _ = lager_id_from_site(site)
    require_admin(x_admin_token)
    return {"ok": True}

@app.post("/api/{site}/admin/workers")
def admin_add_worker(site: str, payload: NameIn, x_admin_token: Optional[str] = Header(None)):
    _ = lager_id_from_site(site)
    require_admin(x_admin_token)
    name = " ".join((payload.name or "").split()).strip()
    if not name:
        raise HTTPException(400, "Missing name")

    con = get_conn()
    try:
        con.execute("INSERT OR IGNORE INTO workers(name, active) VALUES (?, 1)", (name,))
        con.commit()
        return {"ok": True}
    finally:
        con.close()

@app.patch("/api/{site}/admin/workers/{wid}/rename")
def admin_rename_worker(site: str, wid: int, payload: NameIn, x_admin_token: Optional[str] = Header(None)):
    _ = lager_id_from_site(site)
    require_admin(x_admin_token)
    name = " ".join((payload.name or "").split()).strip()
    if not name:
        raise HTTPException(400, "Missing name")

    con = get_conn()
    try:
        cur = con.execute("UPDATE workers SET name=? WHERE id=?", (name, wid))
        con.commit()
        if cur.rowcount == 0:
            raise HTTPException(404, "Worker not found")
        return {"ok": True}
    finally:
        con.close()

@app.patch("/api/{site}/admin/workers/{wid}/active")
def admin_worker_active(site: str, wid: int, payload: ActiveIn, x_admin_token: Optional[str] = Header(None)):
    _ = lager_id_from_site(site)
    require_admin(x_admin_token)

    con = get_conn()
    try:
        cur = con.execute("UPDATE workers SET active=? WHERE id=?", (1 if payload.active else 0, wid))
        con.commit()
        if cur.rowcount == 0:
            raise HTTPException(404, "Worker not found")
        return {"ok": True}
    finally:
        con.close()

@app.patch("/api/{site}/admin/products/{pid}/active")
def admin_product_active(site: str, pid: int, payload: ActiveIn, x_admin_token: Optional[str] = Header(None)):
    _ = lager_id_from_site(site)
    require_admin(x_admin_token)

    con = get_conn()
    try:
        cur = con.execute("UPDATE products SET active=? WHERE id=?", (1 if payload.active else 0, pid))
        con.commit()
        if cur.rowcount == 0:
            raise HTTPException(404, "Product not found")
        return {"ok": True}
    finally:
        con.close()

@app.post("/api/{site}/admin/products")
def admin_add_product(site: str, payload: ProductCreateIn, x_admin_token: Optional[str] = Header(None)):
    _ = lager_id_from_site(site)
    require_admin(x_admin_token)

    kind = (payload.kind or "").strip().lower()
    if kind not in ("netcom", "werkzeug"):
        raise HTTPException(400, "Invalid kind")

    nc_nummer = (payload.nc_nummer or "").strip()
    materialkurztext = (payload.materialkurztext or "").strip()
    product_name = (payload.product_name or "").strip()

    if kind == "netcom":
        if not nc_nummer or not materialkurztext:
            raise HTTPException(400, "Missing nc_nummer or materialkurztext")
    else:
        if not product_name:
            raise HTTPException(400, "Missing product_name")

    con = get_conn()
    try:
        cur = con.cursor()

        cur.execute(
            """
            INSERT INTO products(kind, nc_nummer, materialkurztext, product_name, active)
            VALUES (?, ?, ?, ?, 1)
            """,
            (kind, nc_nummer if kind == "netcom" else None,
             materialkurztext if kind == "netcom" else None,
             product_name if kind == "werkzeug" else None),
        )
        new_id = cur.lastrowid

        # Ensure stock rows exist for both lagers (1=Konstanz, 2=Sindelfingen)
        for lager_id in (1, 2):
            cur.execute(
                "INSERT OR IGNORE INTO stock(lager_id, product_id, quantity) VALUES (?, ?, 0)",
                (lager_id, new_id),
            )

        con.commit()
        return {"ok": True, "id": new_id}
    finally:
        con.close()
