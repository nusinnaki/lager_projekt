from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from backend.db import get_conn

app = FastAPI(title="POPSITE Lager API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Movement(BaseModel):
    worker_id: int
    product_id: int
    qty: int = Field(..., gt=0)

def _change_stock(site: str, worker_id: int, product_id: int, qty: int, action: str):
    action = action.upper().strip()
    if action not in ("TAKE", "LOAD"):
        raise HTTPException(status_code=400, detail="Invalid action")

    delta = qty if action == "LOAD" else -qty

    try:
        con = get_conn(site)
    except ValueError:
        raise HTTPException(status_code=404, detail="Unknown storage")

    cur = con.cursor()

    w = cur.execute(
        "SELECT id FROM workers WHERE id=? AND active=1",
        (worker_id,)
    ).fetchone()
    if not w:
        con.close()
        raise HTTPException(status_code=400, detail="Worker not found or inactive")

    p = cur.execute(
        "SELECT id FROM products WHERE id=?",
        (product_id,)
    ).fetchone()
    if not p:
        con.close()
        raise HTTPException(status_code=400, detail="Product not found")

    cur.execute(
        "INSERT OR IGNORE INTO stock(product_id, quantity) VALUES (?, 0)",
        (product_id,)
    )
    current = cur.execute(
        "SELECT quantity FROM stock WHERE product_id=?",
        (product_id,)
    ).fetchone()["quantity"]

    new_qty = current + delta
    if new_qty < 0:
        con.close()
        raise HTTPException(status_code=400, detail=f"Not enough stock. Current: {current}")

    cur.execute(
        "UPDATE stock SET quantity=? WHERE product_id=?",
        (new_qty, product_id)
    )

    cur.execute(
        "INSERT INTO logs(ts, action, worker_id, product_id, quantity, delta) "
        "VALUES(datetime('now'), ?, ?, ?, ?, ?)",
        (action, worker_id, product_id, qty, delta)
    )

    con.commit()
    con.close()

@app.get("/api/{site}/workers")
def workers(site: str):
    try:
        con = get_conn(site)
    except ValueError:
        raise HTTPException(status_code=404, detail="Unknown storage")

    rows = con.execute(
        "SELECT id, name FROM workers WHERE active=1 ORDER BY name"
    ).fetchall()
    con.close()
    return [{"id": r["id"], "name": r["name"]} for r in rows]

@app.get("/api/{site}/products")
def products(site: str):
    try:
        con = get_conn(site)
    except ValueError:
        raise HTTPException(status_code=404, detail="Unknown storage")

    rows = con.execute(
        "SELECT id, name FROM products ORDER BY name"
    ).fetchall()
    con.close()
    return [{"id": r["id"], "name": r["name"]} for r in rows]

@app.get("/api/{site}/stock")
def stock(site: str, limit: int = 500):
    try:
        con = get_conn(site)
    except ValueError:
        raise HTTPException(status_code=404, detail="Unknown storage")

    rows = con.execute(
        """
        SELECT p.id AS product_id, p.name AS name, s.quantity AS quantity
        FROM products p
        JOIN stock s ON s.product_id = p.id
        ORDER BY p.name
        LIMIT ?
        """,
        (limit,)
    ).fetchall()
    con.close()
    return [{"product_id": r["product_id"], "name": r["name"], "quantity": r["quantity"]} for r in rows]

@app.post("/api/{site}/take")
def take(site: str, m: Movement):
    _change_stock(site, m.worker_id, m.product_id, m.qty, "TAKE")
    return {"ok": True}

@app.post("/api/{site}/load")
def load(site: str, m: Movement):
    _change_stock(site, m.worker_id, m.product_id, m.qty, "LOAD")
    return {"ok": True}

@app.get("/api/{site}/logs")
def logs(site: str, limit: int = 200):
    try:
        con = get_conn(site)
    except ValueError:
        raise HTTPException(status_code=404, detail="Unknown storage")

    rows = con.execute(
        """
        SELECT l.id, l.ts, l.action, w.name AS worker, p.name AS product, l.quantity, l.delta
        FROM logs l
        JOIN workers w ON w.id = l.worker_id
        JOIN products p ON p.id = l.product_id
        ORDER BY l.id DESC
        LIMIT ?
        """,
        (limit,)
    ).fetchall()
    con.close()
    return [
        {
            "id": r["id"],
            "ts": r["ts"],
            "action": r["action"],
            "worker": r["worker"],
            "product": r["product"],
            "quantity": r["quantity"],
            "delta": r["delta"],
        }
        for r in rows
    ]
