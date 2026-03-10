from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = BASE_DIR / "frontend"


@router.get("/")
def serve_index():
    return FileResponse(FRONTEND_DIR / "index.html")


@router.get("/lager")
def serve_lager():
    return FileResponse(FRONTEND_DIR / "lager.html")


@router.get("/admin")
def serve_admin():
    return FileResponse(FRONTEND_DIR / "admin.html")


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}
