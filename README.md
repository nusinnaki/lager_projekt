````markdown
# POPSITE Lager Tool

Local web-based inventory management system.

- FastAPI backend (SQLite)
- Static HTML/JS frontend
- Worker & product management
- Stock tracking with logging
- QR-based product selection
- Admin-protected endpoints

---

# Requirements

- Python 3.9+
- pip
- Git

---

# Quick Start (Recommended)

## 1. Clone the Repository

```bash
git clone https://github.com/nusinnaki/lager_projekt.git
cd lager_projekt
````

---

## 2. Install pipenv (only once)

```bash
python3 -m pip install --user pipenv
```

If `pipenv` is not found after installation:

```bash
echo 'export PATH="$HOME/Library/Python/3.9/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

---

## 3. Install Dependencies

```bash
pipenv sync
```

This installs all backend dependencies from `Pipfile.lock`.

---

## 4. Start the Website

Use the provided development script:

```bash
chmod +x run_dev.sh
./run_dev.sh
```

This will automatically:

* Start backend on `http://127.0.0.1:8000`
* Start frontend on `http://127.0.0.1:5500`
* Set development admin token to:

```
popsite
```

---

# Open in Browser

```
http://127.0.0.1:5500/?site=konstanz
```

or

```
http://127.0.0.1:5500/?site=sindelfingen
```

Do **NOT** open HTML files via `file://`.

Camera scanning only works when served via HTTP.

---

# Admin Access

Admin token for development:

```
popsite
```

Admin allows:

* Add workers
* Activate/deactivate workers
* Add products
* Activate/deactivate products

Admin requests use header:

```
X-Admin-Token: <token>
```

---

# How the System Works

## Backend

Runs on port **8000**

Main files:

* `backend/main.py`
* `backend/db.py`
* `backend/schema.sql`

Database:

```
db/Lager_live.db
```

---

## Frontend

Runs on port **5500**

Main files:

* `frontend/index.html`
* `frontend/lager.html`
* `frontend/api.js`
* `frontend/take_load.js`
* `frontend/admin.js`
* `frontend/qr.js`

---

# QR Workflow

* QR payload = product `id`
* Scan selects product automatically
* Perform TAKE or LOAD
* Camera requires HTTP origin

---

# Troubleshooting

## Port already in use

```bash
lsof -ti tcp:8000 | xargs kill -9
lsof -ti tcp:5500 | xargs kill -9
```

---

## Admin not working

* Ensure you started with `./run_dev.sh`
* Use token: `popsite`
* Restart script if needed

---

System runs fully locally.
No external services required.

After cloning and running `./run_dev.sh`, the project is ready to use.

```
```
