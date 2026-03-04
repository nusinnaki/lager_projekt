# POPSITE Lager Tool

Local web-based inventory management system.

- FastAPI backend (SQLite)
- Static HTML/JS frontend
- Worker and product management
- Stock tracking with logging
- QR-based product selection
- Admin-protected endpoints

---

## Requirements

- Docker installed

---

## Run with Docker (recommended)
---

```shell
docker build -t lager-projekt .  
docker run --rm -it -p 8000:8000 -p 5500:5500 lager-projekt:latest
```


## 5. Open in browser

[app](http://localhost:5500/lager.html?site=konstanz)
---


# Important Notes

* Do not open HTML via `file://`
* Camera scanning only works when served via HTTP
* Admin token (development): `popsite`
* If you change the token, restart the backend
* Backend runs on port 8000
* Frontend runs on port 5500

```
```
