from __future__ import annotations

import secrets
from typing import Any

import httpx
from fastapi import HTTPException

from .config import settings
from .database import RefreshPreviewStale, planning_state, production_refresh_inputs, production_sync_status, replace_planning_state_from_production, scenarios
from .production_area import production_area
from .production_merge import refresh_groups, seed_digest, settings_key_differences


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


def _is_scenario_list(value: Any) -> bool:
    if not isinstance(value, list):
        return False
    return all(
        isinstance(item, dict)
        and all(isinstance(item.get(key), str) for key in ("id", "name", "createdAt", "notes"))
        and bool(item["id"].strip())
        and bool(item["name"].strip())
        and isinstance(item.get("seed"), dict)
        and isinstance(item.get("result"), dict)
        for item in value
    )


def production_snapshot(token: str | None) -> dict[str, Any]:
    if settings.app_env.lower() != "production":
        raise HTTPException(status_code=404, detail="Üretim anlık görüntüsü bu ortamda sunulmuyor.")
    if not settings.staging_pull_token:
        raise HTTPException(status_code=503, detail="Staging veri aktarımı üretimde yapılandırılmamış.")
    if not token or not secrets.compare_digest(token, settings.staging_pull_token):
        raise HTTPException(status_code=401, detail="Staging veri aktarım anahtarı geçersiz.")
    state = planning_state()
    area = production_area.get()
    if state is None or not _is_planning_seed(state.get("seed")):
        raise HTTPException(status_code=404, detail="Üretimde kopyalanacak planlama durumu bulunamadı.")
    if state["seed"].get("productionArea", "torna") != area:
        raise HTTPException(status_code=409, detail="Üretimdeki planlama kaydı seçili üretim alanıyla eşleşmiyor.")
    area_scenarios = [item for item in scenarios() if isinstance(item.get("seed"), dict) and item["seed"].get("productionArea", "torna") == area]
    return {"planningState": state, "scenarios": area_scenarios}


def _local_production_sync() -> bool:
    return settings.app_env.lower() == "test" and settings.auth_test_mode and settings.enable_local_production_sync


def production_sync_status_payload() -> dict[str, Any]:
    local_sync = _local_production_sync()
    enabled = (
        (settings.app_env.lower() == "staging" or local_sync)
        and bool(settings.production_api_url)
        and bool(settings.production_sync_token)
    )
    return {
        "appEnv": settings.app_env.lower(),
        "enabled": enabled,
        "lastSync": production_sync_status(),
        **({"target": "local"} if local_sync else {}),
    }


def _fetch_production_source() -> tuple[dict[str, Any], str, list[dict[str, Any]]]:
    """Read the production snapshot for staging or an enabled local session."""
    local_sync = _local_production_sync()
    if settings.app_env.lower() != "staging" and not local_sync:
        raise HTTPException(status_code=403, detail="Üretimden veri alma bu ortamda kullanılamıyor.")
    if not settings.production_api_url or not settings.production_sync_token:
        raise HTTPException(status_code=503, detail="Üretim veri kaynağı yapılandırılmamış." if local_sync else "Staging için üretim veri kaynağı yapılandırılmamış.")

    area = production_area.get()
    unchanged = "Yerel kayıt değiştirilmedi." if local_sync else "staging değiştirilmedi."
    url = f"{settings.production_api_url}/production-snapshot"
    try:
        response = httpx.get(
            url,
            headers={SYNC_HEADER: settings.production_sync_token, "X-Production-Area": area},
            timeout=20.0,
            follow_redirects=False,
        )
    except httpx.RequestError as error:
        raise HTTPException(status_code=502, detail=f"Üretim ortamına bağlanılamadı. {unchanged}") from error
    if response.status_code != 200:
        if area == "cubuk-filtre" and response.status_code in (400, 404, 409):
            raise HTTPException(status_code=502, detail=f"Üretimde Çubuk Filtre verisi alınamıyor. {unchanged}")
        raise HTTPException(status_code=502, detail=f"Üretim verisi okunamadı. {unchanged}")
    response_area = response.headers.get("X-Production-Area")
    if (area == "cubuk-filtre" and response_area != "cubuk-filtre") or (response_area and response_area != area):
        raise HTTPException(status_code=502, detail=f"Üretim ortamı seçili üretim alanını doğrulamadı. {unchanged}")
    try:
        payload = response.json()
    except ValueError as error:
        raise HTTPException(status_code=502, detail=f"Üretim ortamı geçerli veri döndürmedi. {unchanged}") from error

    record = payload.get("planningState") if isinstance(payload, dict) else None
    scenario_records = payload.get("scenarios") if isinstance(payload, dict) else None
    seed = record.get("seed") if isinstance(record, dict) else None
    source_updated_at = record.get("updatedAt") if isinstance(record, dict) else None
    if not _is_planning_seed(seed) or not isinstance(source_updated_at, str) or not source_updated_at or not _is_scenario_list(scenario_records):
        raise HTTPException(status_code=502, detail=f"Üretim planlama kaydı eksik. {unchanged}")
    if seed.get("productionArea", "torna") != area:
        raise HTTPException(status_code=502, detail="Üretimden gelen planlama kaydı seçili üretim alanıyla eşleşmiyor; staging değiştirilmedi.")
    if any(item["seed"].get("productionArea", "torna") != area for item in scenario_records):
        raise HTTPException(status_code=502, detail="Üretimden gelen senaryo kayıtları seçili üretim alanıyla eşleşmiyor; staging değiştirilmedi.")
    return seed, source_updated_at, scenario_records


def _source_digest(seed: dict[str, Any], source_updated_at: str, scenario_records: list[dict[str, Any]]) -> str:
    return seed_digest({"seed": seed, "updatedAt": source_updated_at, "scenarios": scenario_records}) or ""


def _preview(seed: dict[str, Any], source_updated_at: str, scenario_records: list[dict[str, Any]]) -> dict[str, Any]:
    local, local_updated_at, baseline = production_refresh_inputs()
    known = {item.get("id") for item in scenarios()}
    groups = refresh_groups(seed, local, baseline)
    return {
        "sourceUpdatedAt": source_updated_at,
        "sourceDigest": _source_digest(seed, source_updated_at, scenario_records),
        "localUpdatedAt": local_updated_at,
        "localDigest": seed_digest(local),
        "baselineDigest": seed_digest(baseline),
        "baselineMissing": baseline is None,
        "groups": groups,
        "requiresReview": any(group["requiresChoice"] for group in groups),
        "settingsKeys": settings_key_differences(seed, local, baseline),
        "scenarios": {"sourceCount": len(scenario_records), "newIds": [item["id"] for item in scenario_records if item["id"] not in known]},
    }


def preview_production_refresh() -> dict[str, Any]:
    """Read-only comparison of the target with the current production source."""
    return _preview(*_fetch_production_source())


def apply_production_refresh(expected: dict[str, Any], choices: dict[str, str] | None) -> dict[str, Any]:
    """Apply a reviewed preview. The source is read again; any change rejects the write."""
    seed, source_updated_at, scenario_records = _fetch_production_source()
    if expected.get("sourceDigest") != _source_digest(seed, source_updated_at, scenario_records):
        raise HTTPException(status_code=409, detail={"message": "Üretim kaynağı önizlemeden sonra değişti. Önizlemeyi yenileyip yeniden inceleyin.", "preview": _preview(seed, source_updated_at, scenario_records)})
    try:
        return replace_planning_state_from_production(seed, source_updated_at, settings.production_api_url, scenario_records, expected, choices)
    except RefreshPreviewStale as error:
        message = "Yerel kayıt değişti. Önizlemeyi yenileyip yeniden inceleyin." if _local_production_sync() else str(error)
        raise HTTPException(status_code=409, detail={"message": message, "preview": _preview(seed, source_updated_at, scenario_records)}) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


def pull_production_state(action: str | None = None, expected: dict[str, Any] | None = None, choices: dict[str, str] | None = None) -> dict[str, Any]:
    """Route entry (Root wires the body). preview → comparison; apply → reviewed write.

    A body without an action (older client) applies only when no group needs a
    choice; otherwise it returns 409 with the preview. A missing baseline with
    local differences always needs review.
    """
    if action == "preview":
        return preview_production_refresh()
    if action == "apply":
        if not isinstance(expected, dict):
            raise HTTPException(status_code=422, detail="Önizleme bilgisi eksik; önce önizlemeyi açın.")
        return apply_production_refresh(expected, choices)
    if action is not None or _local_production_sync():
        raise HTTPException(status_code=422, detail="Geçersiz yenileme işlemi.")
    seed, source_updated_at, scenario_records = _fetch_production_source()
    preview = _preview(seed, source_updated_at, scenario_records)
    if preview["requiresReview"]:
        raise HTTPException(status_code=409, detail={"message": "Üretim verisi ile staging çalışması çakışıyor. Grupları inceleyip seçim yapın.", "preview": preview})
    expected = {key: preview[key] for key in ("sourceDigest", "localDigest", "localUpdatedAt", "baselineDigest")}
    try:
        return replace_planning_state_from_production(seed, source_updated_at, settings.production_api_url, scenario_records, expected, None)
    except RefreshPreviewStale as error:
        raise HTTPException(status_code=409, detail={"message": str(error), "preview": _preview(seed, source_updated_at, scenario_records)}) from error
