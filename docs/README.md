### POPSITE Lager Tool

### Practical Maintenance Guide

This document explains **how to operate, modify, and maintain the system safely**.
It focuses on **what to change when you want to modify something**, rather than internal architecture theory.

---

# 1. What this system does

The Lager Tool tracks:

* workers
* users (login accounts)
* products
* storage locations (lagers)
* stock quantities
* stock movements (logs)

The system consists of:

* **SQLite database** (stores all data)
* **FastAPI backend** (handles rules and security)
* **HTML/JS frontend** (user interface)

Flow:

```
Browser
  ↓
FastAPI backend
  ↓
repositories (SQL access)
  ↓
SQLite database
```

---

# 2. Where things live in the project

```
lager_projekt/
├── backend/
│   ├── main.py
│   ├── schema.sql
│   ├── seed.py
│   ├── core/
│   │   └── db.py
│   ├── repositories/
│   │   ├── products.py
│   │   ├── workers.py
│   │   ├── users.py
│   │   └── stock.py
│   └── logic/
│       ├── auth.py
│       ├── users.py
│       └── stock.py
├── db/
│   └── Lager_live.db
├── frontend/
├── scripts/
└── data/
```

---

# 3. If you want to change something

This section explains **where to go depending on what you want to modify**.

---

# 4. If you want to add or modify products

Edit:

```
backend/schema.sql
```

Products table contains:

```
id
kind
nc_nummer
materialkurztext
product_name
active
```

To add products:

Use either

```
backend/seed.py
```

or an import script in:

```
scripts/import_products.py
```

After editing schema:

1. recreate the database
2. run `init_db()`
3. reimport data

Never manually add columns to the live DB without updating `schema.sql`.

---

# 5. If you want to change the worker list

Workers are stored in the **workers table**.

Worker queries are defined in:

```
backend/repositories/workers.py
```

Main function:

```
list_workers(con)
```

(returns all workers currently active in the system)

To add or deactivate workers:

You update the database rows in the **workers table**.

Typical worker columns:

```
id
first_name
last_name
active
```

Setting `active = 0` hides the worker without deleting history.

---

# 6. If you want to manage user accounts

User accounts are separate from workers.

Users are stored in:

```
users table
```

User logic lives in:

```
backend/logic/users.py
```

Functions include:

```
create_user()
change_password()
username_from_worker()
```

Example:

```
change_password()
```

(changes the user's login password and updates password_set_at timestamp)

User queries are implemented in:

```
backend/repositories/users.py
```

Important functions:

```
get_user_by_username(con, username)
(gets user record for login)

get_user_by_id(con, id)
(fetches user profile)

list_users(con)
(admin view of all users)
```

---

# 7. If you want to add a new lager location

Storage locations are stored in the **lagers table**.

Example lagers:

```
Konstanz
Sindelfingen
```

To add a new lager:

1. insert a new row in the lagers table
2. create corresponding stock rows for each product

Stock rows are defined in:

```
stock table
```

Structure:

```
lager_id
product_id
quantity
```

Stock queries live in:

```
backend/repositories/stock.py
```

Key function:

```
list_stock_for_lager(con, lager_id)
```

(returns current stock levels for a given warehouse)

---

# 8. If you want to change stock behavior

Stock business rules are in:

```
backend/logic/stock.py
```

Main function:

```
_act(...)
```

This function:

1. checks stock availability
2. increases or decreases quantity
3. writes a log entry

Example behavior:

```
load
```

(adds stock)

```
take
```

(removes stock)

The database writes are executed through repositories.

---

# 9. If you want to view stock history

Every stock change creates a record in the **logs table**.

Logs table columns:

```
id
action
lager_id
worker_id
product_id
quantity
timestamp
```

Example entry:

```
take
product 8
lager Konstanz
quantity 3
timestamp 2026-03-10
```

Logs are shown in the **Logs button** in the Lager page.

The backend endpoint is:

```
/api/logs
```

---

# 10. If you want to change the UI design

Frontend files live in:

```
frontend/
```

Important files:

```
frontend/lager.html
(main inventory page)

frontend/js/pages/lager.js
(main page logic)

frontend/js/features/stock-table.js
(stock table rendering)

frontend/js/features/qr-scan.js
(QR camera scanning)

frontend/css/components.css
(UI styling)
```

Example changes:

If you want to change colors:

```
frontend/css/components.css
```

If you want to change behavior of buttons:

```
frontend/js/pages/lager.js
```

---

# 11. If you want to change the stock warning colors

Traffic light logic is in:

```
frontend/js/features/traffic-lights.js
```

Function:

```
getStockClass(qty)
```

(This function assigns CSS classes depending on stock quantity.)

Example rule:

```
<5  → red
5-10 → yellow
>10 → normal
```

Changing the numbers here adjusts the warning thresholds.

---

# 12. If you want to change authentication

Authentication logic lives in:

```
backend/logic/auth.py
```

Important functions:

```
hash_password()
(converts password into secure hash)

verify_password()
(compares login password to stored hash)

create_access_token()
(generates login token)

get_current_user()
(validates token on every request)

require_admin()
(checks admin permission)
```

---

# 13. What information is encrypted

Passwords are **never stored as plain text**.

Passwords are stored as:

```
bcrypt hash
```

This means:

* the original password cannot be recovered
* only comparison is possible

Process:

```
user password
↓
hash_password()
↓
bcrypt hash stored in DB
```

During login:

```
entered password
↓
verify_password()
↓
compare against stored hash
```

Login tokens are **JWT tokens**.

Tokens contain:

```
user_id
expiration
permissions
```

Tokens are stored in:

```
browser localStorage
```

and sent with every API request.

---

# 14. If something breaks

Use this checklist.

### Error: "no such column"

Cause:

query references column not defined in schema.sql.

Fix:

update query or schema.

---

### Error: empty database

Cause:

backend created a new DB at wrong path.

Fix:

check DB path in `core/db.py`.

---

### Stock changes not saved

Cause:

write not inside transaction.

Fix:

ensure code runs inside:

```
db_session()
```

---

# 15. Key system rules

Never break these.

1. All database connections come from

```
backend/core/db.py
```

2. All schema changes happen in

```
backend/schema.sql
```

3. Repositories contain SQL only.

4. Logic layer contains behavior.

5. main.py only wires the API.

Dependency direction must always remain:

```
main
↓
logic
↓
repositories
↓
core
↓
database
```

No reverse dependencies allowed.

---