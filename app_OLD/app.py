from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
import sqlite3

DB = "db/live.db"

app = FastAPI(title="POPSITE Lager Tool")

def get_db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def fetch_workers():
    con = get_db()
    cur = con.cursor()
    workers = cur.execute(
        "SELECT id, name FROM workers WHERE active=1 ORDER BY name"
    ).fetchall()
    con.close()
    return workers

def fetch_products():
    con = get_db()
    cur = con.cursor()
    products = cur.execute(
        "SELECT id, name FROM products ORDER BY name"
    ).fetchall()
    con.close()
    return products

def fetch_stock(limit: int = 500):
    con = get_db()
    cur = con.cursor()
    rows = cur.execute(
        """
        SELECT p.name AS name, s.quantity AS quantity
        FROM products p
        JOIN stock s ON s.product_id = p.id
        ORDER BY p.name
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    con.close()
    return rows

def change_stock(worker_id: int, product_id: int, qty: int, action: str):
    if qty <= 0:
        raise ValueError("Quantity must be > 0")

    action = action.upper().strip()
    if action not in ("TAKE", "LOAD"):
        raise ValueError("Action must be TAKE or LOAD")

    delta = qty if action == "LOAD" else -qty

    con = get_db()
    cur = con.cursor()

    # Ensure worker exists
    w = cur.execute("SELECT id FROM workers WHERE id=? AND active=1", (worker_id,)).fetchone()
    if not w:
        con.close()
        raise ValueError("Worker not found or inactive")

    # Ensure product exists
    p = cur.execute("SELECT id FROM products WHERE id=?", (product_id,)).fetchone()
    if not p:
        con.close()
        raise ValueError("Product not found")

    # Ensure stock row exists
    cur.execute("INSERT OR IGNORE INTO stock(product_id, quantity) VALUES (?, 0)", (product_id,))
    current = cur.execute("SELECT quantity FROM stock WHERE product_id=?", (product_id,)).fetchone()["quantity"]

    new_qty = current + delta
    if new_qty < 0:
        con.close()
        raise ValueError(f"Not enough stock. Current: {current}")

    cur.execute("UPDATE stock SET quantity=? WHERE product_id=?", (new_qty, product_id))

    # Log (optional): comment this out if you truly want no logs for now
    cur.execute(
        "INSERT INTO logs(ts, action, worker_id, product_id, quantity, delta) "
        "VALUES(datetime('now'), ?, ?, ?, ?, ?)",
        (action, worker_id, product_id, qty, delta),
    )

    con.commit()
    con.close()

@app.get("/", response_class=HTMLResponse)
def home():
    workers = fetch_workers()
    products = fetch_products()
    stock_rows = fetch_stock(limit=500)

    worker_opts = "".join(f"<option value='{w['id']}'>{w['name']}</option>" for w in workers)
    product_opts = "".join(f"<option value='{p['id']}'>{p['name']}</option>" for p in products)

    stock_html = "\n".join(
        f"<tr><td>{r['name']}</td><td style='text-align:right'>{r['quantity']}</td></tr>"
        for r in stock_rows
    )

    return f"""
    <html>
      <head>
        <title>POPSITE Lager</title>
        <style>
          body {{ font-family: Arial; max-width: 1100px; margin: 30px auto; }}
          .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; align-items: start; }}
          .card {{ border: 1px solid #ddd; border-radius: 10px; padding: 16px; }}
          h1 {{ margin-top: 0; }}
          table {{ border-collapse: collapse; width: 100%; }}
          th, td {{ border: 1px solid #ddd; padding: 8px; }}
          th {{ background: #f6f6f6; text-align: left; }}
          input, select {{ width: 100%; padding: 8px; }}
          button {{ padding: 8px 12px; }}
          .muted {{ color: #666; font-size: 12px; }}
        </style>
      </head>

      <body>
        <h1>POPSITE Lager</h1>

        <div class="grid">
          <div class="card">
            <h2>Take products</h2>
            <form method="post" action="/take">
              <label>Worker</label><br>
              <select name="worker_id" required>{worker_opts}</select><br><br>

              <label>Product</label><br>
              <select name="product_id" required>{product_opts}</select><br><br>

              <label>Quantity</label><br>
              <input type="number" name="qty" min="1" required><br><br>

              <button type="submit">Take</button>
            </form>

            <hr>

            <h2>Load products</h2>
            <form method="post" action="/load">
              <label>Worker</label><br>
              <select name="worker_id" required>{worker_opts}</select><br><br>

              <label>Product</label><br>
              <select name="product_id" required>{product_opts}</select><br><br>

              <label>Quantity</label><br>
              <input type="number" name="qty" min="1" required><br><br>

              <button type="submit">Load</button>
            </form>

            <p class="muted">Logs are written to the DB table "logs".</p>
          </div>

          <div class="card">
            <h2>Current stock</h2>

            <input id="search" placeholder="Search product name..." onkeyup="filterTable()"><br><br>

            <table id="stockTable">
              <thead>
                <tr><th>Product</th><th>Qty</th></tr>
              </thead>
              <tbody>
                {stock_html}
              </tbody>
            </table>

            <p class="muted">Showing up to 500 items.</p>
          </div>
        </div>

        <script>
          function filterTable() {{
            const input = document.getElementById("search").value.toLowerCase();
            const rows = document.querySelectorAll("#stockTable tbody tr");
            rows.forEach(r => {{
              const name = r.children[0].innerText.toLowerCase();
              r.style.display = name.includes(input) ? "" : "none";
            }});
          }}
        </script>
      </body>
    </html>
    """

@app.post("/take", response_class=HTMLResponse)
def take(worker_id: int = Form(...), product_id: int = Form(...), qty: int = Form(...)):
    try:
        change_stock(worker_id, product_id, qty, "TAKE")
    except ValueError as e:
        return HTMLResponse(f"<p>Error: {str(e)}</p><p><a href='/'>Back</a></p>", status_code=400)
    return RedirectResponse("/", status_code=303)

@app.post("/load", response_class=HTMLResponse)
def load(worker_id: int = Form(...), product_id: int = Form(...), qty: int = Form(...)):
    try:
        change_stock(worker_id, product_id, qty, "LOAD")
    except ValueError as e:
        return HTMLResponse(f"<p>Error: {str(e)}</p><p><a href='/'>Back</a></p>", status_code=400)
    return RedirectResponse("/", status_code=303)

@app.get("/inventory")
def inventory_json(limit: int = 500):
    rows = fetch_stock(limit=limit)
    return [{"product": r["name"], "quantity": r["quantity"]} for r in rows]

@app.get("/logs")
def logs_json(limit: int = 200):
    con = get_db()
    cur = con.cursor()
    rows = cur.execute(
        """
        SELECT l.id, l.ts, l.action, w.name AS worker, p.name AS product, l.quantity, l.delta
        FROM logs l
        JOIN workers w ON w.id = l.worker_id
        JOIN products p ON p.id = l.product_id
        ORDER BY l.id DESC
        LIMIT ?
        """,
        (limit,),
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
