# POPSITE Lager Tool

Local web-based inventory management system.

- FastAPI backend (SQLite)
- Static HTML/JS frontend
- Worker and product management
- Stock tracking with logging
- QR-based product selection
- Admin-protected endpoints

---

# Requirements
- Docker

---

```shell
docker build -t lager-projekt .  
docker run --rm -it -p 8000:8000 -p 5500:5500 lager-projekt:latest
```

[app](http://localhost:5500/lager.html?site=konstanz)

# 1. Clone the Repository

```bash
git clone https://github.com/nusinnaki/lager_projekt.git
cd lager_projekt
````

---

# START ON macOS / Linux (bash)

## 1. Install pipenv (only once)

```bash
python3 -m pip install --user pipenv
```

If `pipenv` is not found:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.bashrc 2>/dev/null || true
source ~/.zshrc 2>/dev/null || true
```

---

## 2. Install dependencies

```bash
pipenv sync
```

If that fails:

```bash
pipenv install
```

---

## 3. Start backend

From project root:

```bash
export ADMIN_TOKEN="popsite"
pipenv run uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

You should see:

```
Uvicorn running on http://127.0.0.1:8000
```

Leave this terminal open.

---

## 4. Start frontend

Open a second terminal:

```bash
cd frontend
python3 -m http.server 5500
```

---

## 5. Open in browser

```
http://127.0.0.1:5500/?site=konstanz
```

or

```
http://127.0.0.1:5500/?site=sindelfingen
```

---

# START ON Windows (PowerShell)

## 1. Install pipenv (only once)

```powershell
py -m pip install --user pipenv
```

If `pipenv` is not found after installation, restart PowerShell.

---

## 2. Install dependencies

From project root:

```powershell
pipenv sync
```

If that fails:

```powershell
pipenv install
```

---

## 3. Start backend

```powershell
$env:ADMIN_TOKEN="popsite"
pipenv run uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

You must see:

```
Uvicorn running on http://127.0.0.1:8000
```

Keep this window open.

---

## 4. Start frontend

Open a new PowerShell window:

```powershell
cd frontend
py -m http.server 5500
```

---

## 5. Open in browser

```
http://127.0.0.1:5500/?site=konstanz
```

or

```
http://127.0.0.1:5500/?site=sindelfingen
```

---

# If the port is blocked

Sometimes a crashed server keeps the port occupied.

macOS / Linux
lsof -ti tcp:8000 | xargs kill -9
lsof -ti tcp:5500 | xargs kill -9

Windows (PowerShell)
Get-NetTCPConnection -LocalPort 8000 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
Get-NetTCPConnection -LocalPort 5500 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }

Then start the servers again.

# Important Notes

* Do not open HTML via `file://`
* Camera scanning only works when served via HTTP
* Admin token (development): `popsite`
* If you change the token, restart the backend
* Backend runs on port 8000
* Frontend runs on port 5500

```
```
