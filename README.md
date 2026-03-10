# POPSITE Lager Tool

Local web-based inventory management system.

Features:

* FastAPI backend with SQLite database
* Built-in frontend served by the backend
* Worker and product management
* Stock tracking with full log history
* QR-based product selection
* Admin-protected endpoints
* Single-server architecture

The FastAPI server serves:

* API endpoints
* HTML pages
* JavaScript
* CSS
* static assets

---

# Requirements

Docker must be installed.

Installation guide:

[https://docs.docker.com/get-docker/](https://docs.docker.com/get-docker/)

---

# 1. Clone the repository

```bash
git clone https://github.com/nusinnaki/lager_projekt.git
cd lager_projekt
```

---

# 2. Build the Docker image

```bash
docker build -t lager-projekt .
```

This builds the application image using the provided Dockerfile.

---

# 3. Run the container

```bash
docker run --rm -it -p 8000:8000 lager-projekt
```

Explanation:

```
-p 8000:8000
```

maps the container's port 8000 to your local machine.

---

# 4. Open the application

Open your browser:

```
http://localhost:8000
```

Main pages:

```
http://localhost:8000/        → Login
http://localhost:8000/lager   → Inventory system
http://localhost:8000/admin   → Admin panel
```

---

# Important Notes

### Do not open HTML files directly

Do **not** open files using:

```
file://frontend/lager.html
```

The application requires the backend server to function.

Always access the system through:

```
http://localhost:8000
```

---

### Camera access (QR scanning)

QR scanning requires the page to be served over HTTP.

Docker already provides this through the FastAPI server.

---

### Ports used

Only **one port is required**:

```
8000 → FastAPI server
```

The server provides:

* API
* frontend pages
* static files

No separate frontend server is needed.

---

### Database

The application uses a local SQLite database stored in:

```
db/Lager_live.db
```

The database is automatically initialized at startup if it does not exist.

---

### Stopping the container

Press:

```
CTRL + C
```

The container will stop and be removed because of the `--rm` flag.

---

### Rebuilding after code changes

If you modify the source code, rebuild the image:

```bash
docker build -t lager-projekt .
```

Then run the container again.

---

This Docker setup runs the entire application with a **single FastAPI server and a single exposed port**.
