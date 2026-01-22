from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.db import get_conn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ActionIn(BaseModel):
    worker: str          # worker id (as string) OR worker name (fallback)
    product_id: int
    quantity: int

def _worker_id(con, worker_value: str) -> int:
    cur = con.cursor()
    w = (worker_value or "").strip()
    if not w:
        raise HTTPException(400, "Missing worker")

    # try numeric id
    if w.isdigit():
        row = cur.execute("SELECT id FROM workers WHERE id=? AND active=1", (int(w),)).fetchone()
        if row:
            return row["id"]

    # fallback: by name
    row = cur.execute("SELECT id FROM workers WHERE name=? AND active=1", (w,)).fetchone()
    if row:
        return row["id"]

    raise HTTPException(400, "Unknown worker")

@app.get("/api/{site}/workers")
def workers(site: str):
    con = get_conn(site)
    rows = con.execute("SELECT id, name FROM workers WHERE active=1 ORDER BY name;").fetchall()
    con.close()
    return [dict(r) for r in rows]

@app.get("/api/{site}/products")
def products(site: str):
    con = get_conn(site)
    rows = con.execute("SELECT id, product_name, internal_id, qr_code FROM products ORDER BY product_name;").fetchall()
    con.close()
    return [dict(r) for r in rows]

@app.get("/api/{site}/stock")
def stock(site: str):
    con = get_conn(site)
    rows = con.execute("""
        SELECT p.id AS product_id, p.product_name, p.internal_id, p.qr_code, s.quantity
        FROM stock s
        JOIN products p ON p.id = s.product_id
        ORDER BY p.product_name;
    """).fetchall()
    con.close()
    return [dict(r) for r in rows]

@app.get("/api/{site}/resolve")
def resolve(site: str, code: str):
    con = get_conn(site)
    row = con.execute(
        "SELECT id, product_name, internal_id, qr_code FROM products WHERE qr_code=? LIMIT 1",
        (code.strip(),),
    ).fetchone()
    con.close()
    if not row:
        raise HTTPException(status_code=404, detail="Unknown code")
    return dict(row)

def _apply_action(site: str, action: str, payload: ActionIn):
    if payload.quantity <= 0:
        raise HTTPException(400, "Quantity must be > 0")

    con = get_conn(site)
    cur = con.cursor()

    wid = _worker_id(con, payload.worker)
    row = cur.execute("SELECT quantity FROM stock WHERE product_id=?", (payload.product_id,)).fetchone()
    if row is None:
        con.close()
        raise HTTPException(400, "Unknown product_id")

    current = int(row["quantity"])
    if action == "take":
        newq = current - payload.quantity
        if newq < 0:
            con.close()
            raise HTTPException(400, "Not enough stock")
    else:
        newq = current + payload.quantity

    cur.execute("UPDATE stock SET quantity=? WHERE product_id=?", (newq, payload.product_id))
    cur.execute(
        "INSERT INTO logs(action, worker_id, product_id, quantity, site) VALUES (?, ?, ?, ?, ?)",
        (action, wid, payload.product_id, payload.quantity, site),
    )
    con.commit()
    con.close()
    return {"ok": True, "new_quantity": newq}

@app.post("/api/{site}/take")
def take(site: str, payload: ActionIn):
    return _apply_action(site, "take", payload)

@app.post("/api/{site}/load")
def load(site: str, payload: ActionIn):
    return _apply_action(site, "load", payload)
