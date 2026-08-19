from __future__ import annotations

import secrets
from typing import Any

import httpx
from fastapi import HTTPException

from .config import settings
from .database import planning_state, production_sync_status, replace_planning_state_from_production


SYNC_HEADER = "X-Staging-Pull-Token"


def _is_planning_seed(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    collections = ("machines", "products", "preferences", "orders")
    if not all(isinstance(value.get(key), list) for key in collections):
        return False
    if not all(isinstance(item, dict) for key in collections for item in value[key]):
        return False
    required_identity = {
        "machines": "id",
        "products": "product",
        "preferences": "key",
        "orders": "id",
    }
    return all(
        isinstance(item.get(identity), str) and bool(item[identity].strip())
        for collection, identity in required_identity.items()
        for item in value[collection]
    )


def production_snapshot(token: str | None) -> dict[str, Any]:
    if settings.app_env.lower() != "production":
        raise HTTPException(status_code=404, detail="Üretim anlık görüntüsü bu ortamda sunulmuyor.")
    if not settings.staging_pull_token:
        raise HTTPException(status_code=503, detail="Staging veri aktarımı üretimde yapılandırılmamış.")
    if not token or not secrets.compare_digest(token, settings.staging_pull_token):
        raise HTTPException(status_code=401, detail="Staging veri aktarım anahtarı geçersiz.")
    state = planning_state()
    if state is None or not _is_planning_seed(state.get("seed")):
        raise HTTPException(status_code=404, detail="Üretimde kopyalanacak planlama durumu bulunamadı.")
    return {"planningState": state}


def production_sync_status_payload() -> dict[str, Any]:
    enabled = (
        settings.app_env.lower() == "staging"
        and bool(settings.production_api_url)
        and bool(settings.production_sync_token)
    )
    return {
        "appEnv": settings.app_env.lower(),
        "enabled": enabled,
        "lastSync": production_sync_status(),
    }


def pull_production_state() -> dict[str, Any]:
    if settings.app_env.lower() != "staging":
        raise HTTPException(status_code=403, detail="Üretimden veri alma yalnızca staging ortamında kullanılabilir.")
    if not settings.production_api_url or not settings.production_sync_token:
        raise HTTPException(status_code=503, detail="Staging için üretim veri kaynağı yapılandırılmamış.")

    url = f"{settings.production_api_url}/production-snapshot"
    try:
        response = httpx.get(
            url,
            headers={SYNC_HEADER: settings.production_sync_token},
            timeout=20.0,
            follow_redirects=False,
        )
    except httpx.RequestError as error:
        raise HTTPException(status_code=502, detail="Üretim ortamına bağlanılamadı; staging değiştirilmedi.") from error
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Üretim verisi okunamadı; staging değiştirilmedi.")
    try:
        payload = response.json()
    except ValueError as error:
        raise HTTPException(status_code=502, detail="Üretim ortamı geçerli veri döndürmedi; staging değiştirilmedi.") from error

    record = payload.get("planningState") if isinstance(payload, dict) else None
    seed = record.get("seed") if isinstance(record, dict) else None
    source_updated_at = record.get("updatedAt") if isinstance(record, dict) else None
    if not _is_planning_seed(seed) or not isinstance(source_updated_at, str) or not source_updated_at:
        raise HTTPException(status_code=502, detail="Üretim planlama kaydı eksik; staging değiştirilmedi.")

    return replace_planning_state_from_production(seed, source_updated_at, settings.production_api_url)
