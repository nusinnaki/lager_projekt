# POPSITE Lager Tool

Web-based inventory tool with:
- FastAPI backend (SQLite)
- Static HTML/JS frontend
- Admin panel for managing workers and products
- Take/Load stock actions with logging
- QR workflow for Netcom products (QR payload equals product id)

## Project structure

- backend/
  - main.py: FastAPI app and API routes
  - db.py: SQLite connection helpers
  - schema.sql: database schema
  - seed.py: one-time database seeding
- frontend/
  - index.html: site selection landing page
  - lager.html: inventory UI (take/load, stock table, admin, scanner)
  - styles.css: shared styling
  - api.js: API base + fetch helpers
  - take_load.js: load workers/products/stock and perform take/load actions
  - admin.js: admin UI logic (workers/products CRUD, activation)
  - qr.js: QR input and camera scan integration
  - assets/: logo and site images
- db/
  - Lager_live.db: SQLite database (local)
- data/ (ignored)
  - local CSV/PDF/assets for importing and QR label output
- scripts/ (ignored)
  - helper scripts (imports, QR label generation)

## How it works

### 1) Backend startup
1. Loads environment variable `ADMIN_TOKEN` (required for admin endpoints).
2. Opens SQLite database from `db/`.
3. Serves REST API under:
   - `/api/{site}/workers`
   - `/api/{site}/products`
   - `/api/{site}/stock`
   - `/api/{site}/take`
   - `/api/{site}/load`
   - `/api/{site}/admin/...`

### 2) Database model (high level)
- `workers`
  - immutable integer `id` (internal)
  - `name`
  - `active` flag
- `products`
  - immutable integer `id` (this is the QR payload for Netcom products)
  - `kind`:
    - `netcom`: uses `nc_nummer` + `materialkurztext`
    - `werkzeug`: uses `product_name`
  - `active` flag
- `stock`
  - one row per product id, holds current quantity
- `logs`
  - records take/load actions (who, what, how much, site, timestamp)

### 3) Frontend flow

#### Landing page (index.html)
1. Shows two site cards (Konstanz, Sindelfingen).
2. Clicking a card opens:
   - `lager.html?site=konstanz`
   - `lager.html?site=sindelfingen`

#### Lager page (lager.html)
1. `api.js` reads `site` from the query string and sets API base:
   - `http://127.0.0.1:8000/api/<site>`
2. `take_load.js` loads:
   - active workers into Worker dropdown
   - active products into Product dropdown (labels differ by kind)
   - stock table into “Current stock”
3. User chooses action mode:
   - LOAD or TAKE
4. User selects:
   - worker
   - product (dropdown) or QR scan
   - quantity
5. On action button click:
   - frontend sends POST `/take` or `/load`
   - backend validates and updates stock
   - frontend reloads stock table and shows status message

### 4) Admin panel
1. User enters admin token (must match backend `ADMIN_TOKEN`).
2. Admin endpoints require header:
   - `X-Admin-Token: <token>`
3. Workers:
   - add
   - rename
   - deactivate
   - reactivate
4. Products:
   - add Netcom product (NC Nummer + Materialkurztext)
   - add Werkzeug product (Produkt Name)
   - deactivate product (keeps id stable; active flag changes)

### 5) QR workflow
- For Netcom products, QR payload equals the immutable product `id`.
- Phone camera scan reads the QR payload (e.g. `37`).
- Frontend uses that value to select the matching product id.
- The action then applies to the correct product row in the database.

## Run locally

```bash
git clone <repo>
cd project

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python backend/main.py
```
