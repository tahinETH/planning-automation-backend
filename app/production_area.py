"""Request-local production scope. Authentication remains application-wide."""
from contextvars import ContextVar
from pathlib import Path
import sqlite3
from typing import Any

from starlette.responses import JSONResponse
from .config import settings

production_area: ContextVar[str] = ContextVar("production_area", default="torna")
AREAS = {"torna", "cubuk-filtre"}


def area_available(area: str) -> bool:
    if area not in AREAS:
        return False
    if area == "torna" or settings.app_env != "production":
        return True
    if not getattr(settings, "enable_filter_production", False):
        return False
    # A production Filter workspace must have an accepted offline opening.
    # Read the Filter database even when listing areas from a Piston request.
    path = area_database_path(settings.database_path, area)
    if not path.is_file():
        return False
    from contextlib import closing
    with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('production_handover','planning_state','production_opening')")}
        if len(tables) != 3:
            return False
        return db.execute("""SELECT 1 FROM production_handover h, planning_state s, production_opening o
            WHERE h.id='default' AND s.state_key='default' AND o.id='default'""").fetchone() is not None


def area_database_path(path: Path, area: str | None = None) -> Path:
    return path if (area or production_area.get()) == "torna" else path.with_name(f"{path.stem}-cubuk-filtre{path.suffix}")


def validate_seed_area(seed: dict[str, Any]) -> None:
    if seed.get("productionArea", "torna") != production_area.get():
        raise ValueError("Bu kayıt başka bir üretim alanına ait. Doğru üretim alanını seçin.")


class ProductionAreaMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = dict(scope.get("headers", []))
        area = headers.get(b"x-production-area", b"torna").decode("latin1")
        if not area_available(area):
            return await JSONResponse({"detail": "Üretim alanı bu ortamda kullanılamıyor."}, status_code=400)(scope, receive, send)
        if area == "cubuk-filtre" and scope["path"].startswith(("/api/production-sync", "/api/production-snapshot")):
            return await JSONResponse({"detail": "Çubuk Filtre için üretimden veri kopyalama tanımlı değil."}, status_code=409)(scope, receive, send)
        token = production_area.set(area)
        try:
            from .handover import generation
            current_generation = generation()
            receipt_read = scope["path"].startswith(("/api/collaboration/requests/", "/api/planning-state/transactions/"))
            if current_generation and (scope["method"] not in {"GET", "HEAD", "OPTIONS"} or receipt_read) and headers.get(b"x-planning-generation", b"").decode("latin1") != current_generation:
                return await JSONResponse({"detail": {"code": "handover-generation", "message": "Üretim başlangıcı değişti. Bekleyen eski isteği göndermeyin; güncel veriyi yeniden yükleyin."}}, status_code=409)(scope, receive, send)
            async def send_scoped(message):
                if message["type"] == "http.response.start":
                    message.setdefault("headers", []).append((b"x-production-area", area.encode()))
                    if current_generation:
                        message["headers"].append((b"x-planning-generation", current_generation.encode()))
                await send(message)
            await self.app(scope, receive, send_scoped)
        finally:
            production_area.reset(token)
