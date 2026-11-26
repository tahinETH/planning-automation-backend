"""Authenticated read-only CPM endpoints and dedicated-token collector endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Response

from ..auth import CurrentUser, current_user
from ..production_area import production_area
from .config import CpmError, is_environment_allowed, load_config, require_enabled, verify_collector_token
from .models import (
    CpmCollectorFailurePayload,
    CpmCollectorHeartbeatPayload,
    CpmPistonSnapshotPayload,
)
from .store import (
    create_refresh_request,
    get_latest_snapshot,
    get_status,
    ingest_snapshot,
    record_failure,
    record_heartbeat,
)


router = APIRouter(prefix="/api/cpm", tags=["cpm"])


def _set_no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"


def _handle_cpm_error(exc: CpmError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail={"code": exc.code, "message": exc.message})


@router.get("/status")
def cpm_status(response: Response, _: CurrentUser = Depends(current_user)):
    _set_no_store(response)
    config = load_config()
    area = production_area.get()
    if not is_environment_allowed(config):
        return {
            "enabled": False,
            "area": area,
            "supported": area == "torna",
            "refreshIntervalSeconds": config.refresh_interval_seconds,
            "lastSnapshot": None,
            "lastAttempt": None,
            "activeRequest": None,
            "collector": {
                "online": False,
                "vpnConnected": False,
                "collectorId": None,
                "lastSeenAt": None,
                "intervalSeconds": None,
                "nextScheduledAt": None,
                "lastError": None,
            },
        }
    try:
        return get_status(config, area)
    except CpmError as exc:
        raise _handle_cpm_error(exc) from exc


@router.get("/piston/latest")
def cpm_piston_latest(response: Response, _: CurrentUser = Depends(current_user)):
    _set_no_store(response)
    config = load_config()
    area = production_area.get()
    if not is_environment_allowed(config):
        return {
            "status": cpm_status(response, _),
            "snapshot": None,
        }
    try:
        return get_latest_snapshot(config, area)
    except CpmError as exc:
        raise _handle_cpm_error(exc) from exc


@router.post("/refresh-request")
def cpm_refresh_request(response: Response, user: CurrentUser = Depends(current_user)):
    _set_no_store(response)
    config = load_config()
    area = production_area.get()
    try:
        require_enabled(config)
        if area != "torna":
            raise CpmError("area-not-supported", "CPM yenilemesi şu an yalnızca Piston alanı için desteklenir.", status_code=400)
        return create_refresh_request(config, area, user.id)
    except CpmError as exc:
        raise _handle_cpm_error(exc) from exc


@router.post("/collector/heartbeat")
def cpm_collector_heartbeat(
    payload: CpmCollectorHeartbeatPayload,
    response: Response,
    x_cpm_collector_token: str | None = Header(default=None, alias="X-CPM-Collector-Token"),
):
    _set_no_store(response)
    config = load_config()
    try:
        verify_collector_token(config, x_cpm_collector_token)
        return record_heartbeat(config, payload)
    except CpmError as exc:
        raise _handle_cpm_error(exc) from exc


@router.post("/collector/ingest")
def cpm_collector_ingest(
    payload: CpmPistonSnapshotPayload,
    response: Response,
    x_cpm_collector_token: str | None = Header(default=None, alias="X-CPM-Collector-Token"),
):
    _set_no_store(response)
    config = load_config()
    try:
        verify_collector_token(config, x_cpm_collector_token)
        return ingest_snapshot(config, payload)
    except CpmError as exc:
        raise _handle_cpm_error(exc) from exc


@router.post("/collector/failure")
def cpm_collector_failure(
    payload: CpmCollectorFailurePayload,
    response: Response,
    x_cpm_collector_token: str | None = Header(default=None, alias="X-CPM-Collector-Token"),
):
    _set_no_store(response)
    config = load_config()
    try:
        verify_collector_token(config, x_cpm_collector_token)
        return record_failure(config, payload)
    except CpmError as exc:
        raise _handle_cpm_error(exc) from exc
