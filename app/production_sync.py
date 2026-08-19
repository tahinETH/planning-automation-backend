from __future__ import annotations

import secrets
from typing import Any

from fastapi import HTTPException

from .config import settings
from .database import planning_state, scenarios


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
    """Return production state to staging without exposing any write operation."""
    if settings.app_env.lower() != "production":
        raise HTTPException(status_code=404, detail="Üretim anlık görüntüsü bu ortamda sunulmuyor.")
    if not settings.staging_pull_token:
        raise HTTPException(status_code=503, detail="Staging veri aktarımı üretimde yapılandırılmamış.")
    if not token or not secrets.compare_digest(token, settings.staging_pull_token):
        raise HTTPException(status_code=401, detail="Staging veri aktarım anahtarı geçersiz.")
    state = planning_state()
    if state is None or not _is_planning_seed(state.get("seed")):
        raise HTTPException(status_code=404, detail="Üretimde kopyalanacak planlama durumu bulunamadı.")
    return {"planningState": state, "scenarios": scenarios()}
