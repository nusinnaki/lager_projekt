# POPSITE Lager Tool

Local web-based inventory management system.

Features:

* Worker management
* Product management
* Product location assignment
* Stock loading and removal
* Stock tracking with full log history
* QR code scanning and batch QR code printing
* Admin management interface
* FastAPI backend with SQLite database
* Built-in frontend served by the backend
* Single-server architecture

The FastAPI server serves:

* API endpoints
* HTML pages
* JavaScript
* CSS
* Static assets

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

```text
-p 8000:8000
```

maps the container's port 8000 to your local machine.

### Persistent database storage

To keep the SQLite database even after the container stops, mount the local `db/` folder into the container:

```bash
docker run --rm -it \
  -p 8000:8000 \
  -v $(pwd)/db:/app/db \
  lager-projekt
```

Without the volume mount, a newly created container may start with a fresh database.

---

# 4. Open the application

Open your browser:

```text
http://localhost:8000
```

Main pages:

```text
http://localhost:8000/        → Login
http://localhost:8000/lager   → Inventory system
http://localhost:8000/admin   → Admin panel
```

---

# Important Notes

### Do not open HTML files directly

Do **not** open files using:

```text
file://frontend/lager.html
```

The application requires the backend server to function.

Always access the system through:

```text
http://localhost:8000
```

---

### Camera access (QR scanning)

QR scanning requires the application to be served through the FastAPI server.

Opening frontend files directly with `file://` will not allow camera access or API communication.

Docker already provides this through the FastAPI server.

---

### Ports used

Only **one port is required**:

```text
8000 → FastAPI server
```

The server provides:

* API endpoints
* Frontend pages
* Static files

No separate frontend server is needed.

---

### Database

The application uses a local SQLite database stored in:

```text
db/Lager_live.db
```

If the database file does not exist, the application initializes the schema automatically.

---

### Stopping the container

Press:

```text
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

This Docker setup runs the entire application with a single FastAPI server and a single exposed port.



## Data files

This repository does not include the real worker and product data files.

The worker and product data contain internal company information and are therefore excluded from Git using `.gitignore`.

To run the application with real data, request the required data files from the project maintainer.

Expected local data location:

```text
data/
  workers.csv
  products.csv
```

After receiving the files, place them in the `data/` folder before starting the application.