"""Request-local production scope. Authentication remains application-wide."""
from contextvars import ContextVar
from pathlib import Path
from typing import Any

from starlette.responses import JSONResponse
from .config import settings

production_area: ContextVar[str] = ContextVar("production_area", default="torna")
AREAS = {"torna", "cubuk-filtre"}


def area_database_path(path: Path) -> Path:
    return path if production_area.get() == "torna" else path.with_name(f"{path.stem}-cubuk-filtre{path.suffix}")


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
        if area not in AREAS or area == "cubuk-filtre" and settings.app_env == "production":
            return await JSONResponse({"detail": "Üretim alanı bu ortamda kullanılamıyor."}, status_code=400)(scope, receive, send)
        if area == "cubuk-filtre" and scope["path"].startswith(("/api/production-sync", "/api/production-snapshot")):
            return await JSONResponse({"detail": "Çubuk Filtre için üretimden veri kopyalama tanımlı değil."}, status_code=409)(scope, receive, send)
        token = production_area.set(area)
        async def send_scoped(message):
            if message["type"] == "http.response.start":
                message.setdefault("headers", []).append((b"x-production-area", area.encode()))
            await send(message)
        try:
            await self.app(scope, receive, send_scoped)
        finally:
            production_area.reset(token)
