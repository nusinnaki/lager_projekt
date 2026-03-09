# POPSITE Lager Tool

Local web-based inventory management system.

- FastAPI backend with SQLite
- Static HTML/JS frontend
- Login with worker-based accounts
- Stock tracking with logging
- QR-based stock workflow

## Requirements

- Docker

Install Docker if needed:

https://docs.docker.com/get-docker/

## 1. Clone the repo

```shell
git clone https://github.com/nusinnaki/lager_projekt.git
cd lager_projekt
2. Run with Docker
docker build -t lager-projekt .
docker run --rm -it -p 8000:8000 -p 5500:5500 lager-projekt:latest
3. Open in browser

After the container is running, open:

http://localhost:5500/index.html
Login

Current internal login format:

username: name.lastname
password: popsite1234

After login, the main workflow continues in the Lager page.

Important notes

Do not open HTML files with file://

Camera scanning only works when served over HTTP

Backend runs on port 8000

Frontend runs on port 5500

If you change backend code, rebuild the Docker image