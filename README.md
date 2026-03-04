# POPSITE Lager Tool

Local web-based inventory management system.

- FastAPI backend (SQLite)
- Static HTML/JS frontend
- Worker and product management
- Stock tracking with logging
- QR-based product selection
- Admin-protected endpoints


## Requirements

- Docker

Install Docker if needed:

https://docs.docker.com/get-docker/


## 1. Clone the Repo
```shell
git clone https://github.com/nusinnaki/lager_projekt.git
cd lager_projekt
```

## 2. Run with Docker (recommended)

Run the following on shell 

```shell
docker build -t lager-projekt .  
docker run --rm -it -p 8000:8000 -p 5500:5500 lager-projekt:latest
```


## 3. Open in browser
Once you run the code, click the following

http://localhost:5500/lager.html?site=konstanz


# Important Notes

* Do not open HTML via `file://`
* Camera scanning only works when served via HTTP
* Admin token (development): `popsite`
* If you change the token, restart the backend
* Backend runs on port 8000
* Frontend runs on port 5500

```
```
