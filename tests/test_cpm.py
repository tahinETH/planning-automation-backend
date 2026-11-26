"""Regression tests for isolated read-only CPM Piston snapshot store and collector routes."""
from __future__ import annotations

import hashlib
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from app.auth import create_test_session
from app.cpm.config import CpmConfig, CpmError, validate_store_path
from app.main import app


def _sample_piston_payload(
    *,
    captured_at: str = "2026-11-26T11:30:00+03:00",
    trigger_kind: str = "scheduled-15m",
    request_id: str | None = None,
    drilling_qty: float = 2010.0,
) -> dict:
    return {
        "schemaVersion": 1,
        "area": "torna",
        "company": "17",
        "collectorId": "mac-vpn-collector",
        "triggerKind": trigger_kind,
        "requestId": request_id,
        "startedAt": "2026-11-26T11:29:57+03:00",
        "capturedAt": captured_at,
        "rawMaterialScope": "141+320",
        "rawMaterials": [
            {
                "materialCode": "Z170004",
                "materialName": "[31CrMoV9V+SH+E] [Ø17,2mm]",
                "unit": "KG",
                "depot141Kg": 4708.0,
                "depot320Kg": 1936.93,
                "totalAvailableKg": 6644.93,
                "depot250Kg": 0.0,
                "depot960Kg": 0.0,
                "otherDepots": [],
            }
        ],
        "productStocks": [
            {
                "product": "R902745121",
                "drillingQueueQty": drilling_qty,
                "deburringQueueQty": 129.0,
                "gkmQueueQty": 0.0,
                "gkmCompletedQty": 1978.0,
                "finishedWarehouseQty": 1980.0,
                "consignmentQty": 1987.0,
                "scrapExcludedQty": 4300.0,
                "depots": [
                    {"depotCode": "320", "depotName": "320-Piston", "version": "010", "qty": drilling_qty},
                    {"depotCode": "320", "depotName": "320-Piston", "version": "040", "qty": 129.0},
                    {"depotCode": "196", "depotName": "196-Göz Kontrol", "version": "", "qty": 1978.0},
                    {"depotCode": "145", "depotName": "145-Ürün", "version": "000175", "qty": 1980.0},
                    {"depotCode": "800", "depotName": "800-Konsinye Depo", "version": "000175", "qty": 1987.0},
                ],
            }
        ],
        "workOrders": [
            {
                "uretimNo": "320-2600734",
                "product": "R902745121",
                "targetQty": 2010.0,
                "orderDate": "2026-11-10",
                "orderStatus": 2,
                "currentStage": "gkm-completed",
                "turningMachineCode": "249",
                "turningMachineName": "5-CITIZEN (Cincom)",
                "turningErpCode": "01-16-02-006",
                "turningProducedQty": 2025.0,
                "turningLastRunAt": "2026-11-19T14:55:00+03:00",
                "stages": [
                    {
                        "isemriNo": "UIE000134869",
                        "version": "010",
                        "workCenterCode": "010",
                        "workCenterName": "CNC TORNA",
                        "targetQty": 2010.0,
                        "producedQty": 2025.0,
                        "scrapQty": 0.0,
                        "opStatus": 20,
                        "lastMachineCode": "249",
                        "lastMachineName": "5-CITIZEN (Cincom)",
                        "lastErpCode": "01-16-02-006",
                        "lastRunAt": "2026-11-19T14:55:00+03:00",
                        "lastShift": "Vardiya1",
                    },
                    {
                        "isemriNo": "UIE000134866",
                        "version": "",
                        "workCenterCode": "290",
                        "workCenterName": "GÖZ KONTROL",
                        "targetQty": 2010.0,
                        "producedQty": 1993.0,
                        "scrapQty": 0.0,
                        "opStatus": 10,
                        "lastMachineCode": "72",
                        "lastMachineName": "GKM-3 TEKNOSKOP",
                        "lastErpCode": "01-21-16-003",
                        "lastRunAt": "2026-11-25T18:08:00+03:00",
                        "lastShift": "Vardiya2",
                    },
                ],
            }
        ],
        "parameters": {
            "bomWeights": [
                {
                    "product": "R902745121",
                    "materialCode": "Z170004",
                    "materialName": "[31CrMoV9V+SH+E] [Ø17,2mm]",
                    "grams": 74.45,
                    "unit": "GRAM",
                }
            ],
            "cycleTimes": [
                {
                    "product": "R902745121",
                    "version": "040",
                    "workCenterCode": "040",
                    "resourceCode": "358",
                    "resourceName": "TBT SL250-4 SELSA",
                    "erpWorkCenterCode": "01-16-09-003",
                    "cycleSeconds": 51.25,
                }
            ],
            "resources": [
                {
                    "resourceCode": "358",
                    "resourceName": "TBT SL250-4 SELSA",
                    "erpWorkCenterCode": "01-16-09-003",
                    "active": True,
                }
            ],
        },
    }


@pytest.fixture(autouse=True)
def initialized_planning_db():
    from app import database
    database.init_database()


@pytest.fixture
def cpm_env(monkeypatch, tmp_path):
    store_file = tmp_path / "cpm-source" / "piston_snapshots.sqlite"
    monkeypatch.setenv("CPM_ENABLED", "true")
    monkeypatch.setenv("CPM_COLLECTOR_TOKEN", "test-collector-secret-token")
    monkeypatch.setenv("CPM_REFRESH_INTERVAL_SECONDS", "900")
    monkeypatch.setenv("CPM_STORE_PATH", str(store_file))
    return store_file


def _auth_headers(role: str = "user", area: str = "torna") -> dict[str, str]:
    token = create_test_session("test-password", role=role)
    return {"Authorization": f"Bearer {token}", "X-Production-Area": area}


def test_cpm_routes_require_authentication_and_respect_disabled_default(monkeypatch, tmp_path):
    monkeypatch.delenv("CPM_ENABLED", raising=False)
    monkeypatch.setenv("CPM_STORE_PATH", str(tmp_path / "cpm.sqlite"))
    client = TestClient(app)

    assert client.get("/api/cpm/status").status_code == 401
    assert client.get("/api/cpm/piston/latest").status_code == 401
    assert client.post("/api/cpm/refresh-request").status_code == 401

    resp = client.get("/api/cpm/status", headers=_auth_headers())
    assert resp.status_code == 200
    assert resp.headers.get("cache-control") == "no-store"
    assert resp.json()["enabled"] is False
    assert client.post("/api/cpm/refresh-request", headers=_auth_headers()).status_code == 503


def test_collector_token_auth_rejects_missing_wrong_or_browser_jwt(cpm_env):
    client = TestClient(app)
    payload = _sample_piston_payload()

    assert client.post("/api/cpm/collector/ingest", json=payload).status_code == 401
    assert client.post(
        "/api/cpm/collector/ingest",
        json=payload,
        headers={"X-CPM-Collector-Token": "wrong-token"},
    ).status_code == 401
    # Browser JWT must never work as collector token
    assert client.post(
        "/api/cpm/collector/ingest",
        json=payload,
        headers=_auth_headers(role="admin"),
    ).status_code == 401


def test_ingest_deduplication_leading_zeros_and_failure_preserves_last_snapshot(cpm_env):
    client = TestClient(app)
    collector_headers = {"X-CPM-Collector-Token": "test-collector-secret-token"}
    payload = _sample_piston_payload()

    first = client.post("/api/cpm/collector/ingest", json=payload, headers=collector_headers)
    assert first.status_code == 200
    first_body = first.json()
    assert first_body["deduplicated"] is False
    assert first_body["counts"]["workOrders"] == 1

    # Replaying identical snapshot returns the same snapshotId without duplicating
    replay = client.post("/api/cpm/collector/ingest", json=payload, headers=collector_headers)
    assert replay.status_code == 200
    assert replay.json()["deduplicated"] is True
    assert replay.json()["snapshotId"] == first_body["snapshotId"]

    # Recording a collector failure keeps the previous accepted snapshot intact
    fail = client.post(
        "/api/cpm/collector/failure",
        json={
            "collectorId": "mac-vpn-collector",
            "area": "torna",
            "triggerKind": "scheduled-15m",
            "errorCode": "vpn-closed",
            "errorMessage": "SELSA VPN tüneli kapalı.",
        },
        headers=collector_headers,
    )
    assert fail.status_code == 200

    latest = client.get("/api/cpm/piston/latest", headers=_auth_headers())
    assert latest.status_code == 200
    data = latest.json()
    assert data["status"]["lastAttempt"]["status"] == "failed"
    assert data["status"]["lastAttempt"]["errorCode"] == "vpn-closed"
    assert data["status"]["lastSnapshot"]["snapshotId"] == first_body["snapshotId"]
    # Leading zeros and separate GKM completed column survive intact
    stock_row = data["snapshot"]["productStocks"][0]
    assert stock_row["gkmCompletedQty"] == 1978.0
    assert stock_row["depots"][0]["version"] == "010"
    assert stock_row["depots"][2]["version"] == ""
    assert stock_row["depots"][3]["version"] == "000175"


def test_on_demand_refresh_request_errors_when_offline_or_vpn_closed_and_completes_when_online(cpm_env):
    client = TestClient(app)
    collector_headers = {"X-CPM-Collector-Token": "test-collector-secret-token"}

    # Offline collector -> immediate 503 error
    offline_req = client.post("/api/cpm/refresh-request", headers=_auth_headers())
    assert offline_req.status_code == 503
    assert offline_req.json()["detail"]["code"] == "collector-offline"

    # Heartbeat with VPN closed -> still immediate 503 error (vpn-disconnected)
    hb_vpn_closed = client.post(
        "/api/cpm/collector/heartbeat",
        json={
            "collectorId": "mac-vpn-collector",
            "area": "torna",
            "vpnConnected": False,
            "intervalSeconds": 900,
        },
        headers=collector_headers,
    )
    assert hb_vpn_closed.status_code == 200
    assert hb_vpn_closed.json()["pendingRequest"] is None

    vpn_req = client.post("/api/cpm/refresh-request", headers=_auth_headers())
    assert vpn_req.status_code == 503
    assert vpn_req.json()["detail"]["code"] == "vpn-disconnected"

    # Heartbeat with VPN open marks collector ready
    hb_online = client.post(
        "/api/cpm/collector/heartbeat",
        json={
            "collectorId": "mac-vpn-collector",
            "area": "torna",
            "vpnConnected": True,
            "intervalSeconds": 900,
            "nextScheduledAt": "2026-11-26T11:45:00+03:00",
        },
        headers=collector_headers,
    )
    assert hb_online.status_code == 200
    assert hb_online.json()["pendingRequest"] is None

    # Now on-demand refresh succeeds and queues pending request
    req1 = client.post("/api/cpm/refresh-request", headers=_auth_headers())
    assert req1.status_code == 200
    req_id = req1.json()["requestId"]
    assert req1.json()["status"] == "pending"
    assert req1.json()["deduplicated"] is False

    # Rapid second click deduplicates to same pending request
    req2 = client.post("/api/cpm/refresh-request", headers=_auth_headers())
    assert req2.status_code == 200
    assert req2.json()["requestId"] == req_id
    assert req2.json()["deduplicated"] is True

    # Next online heartbeat claims the pending request
    hb_claim = client.post(
        "/api/cpm/collector/heartbeat",
        json={
            "collectorId": "mac-vpn-collector",
            "area": "torna",
            "vpnConnected": True,
            "intervalSeconds": 900,
            "nextScheduledAt": "2026-11-26T11:45:00+03:00",
        },
        headers=collector_headers,
    )
    assert hb_claim.status_code == 200
    assert hb_claim.json()["pendingRequest"]["requestId"] == req_id

    # Ingesting with requestId completes the request
    ing = client.post(
        "/api/cpm/collector/ingest",
        json=_sample_piston_payload(trigger_kind="on-demand", request_id=req_id),
        headers=collector_headers,
    )
    assert ing.status_code == 200
    status = client.get("/api/cpm/status", headers=_auth_headers()).json()
    assert status["activeRequest"]["status"] == "completed"
    assert status["activeRequest"]["snapshotId"] == ing.json()["snapshotId"]
    assert status["collector"]["online"] is True
    assert status["collector"]["vpnConnected"] is True


def test_cpm_telegram_alerts_respect_cooldown_and_send_single_recovery(cpm_env, monkeypatch):
    from app.cpm import alerts

    sent: list[tuple[str, str, str]] = []
    monkeypatch.setattr(alerts, "_dispatch_telegram", lambda token, chat_id, text: sent.append((token, chat_id, text)))
    client = TestClient(app)
    collector_headers = {"X-CPM-Collector-Token": "test-collector-secret-token"}

    # Unconfigured by default -> no alert dispatched
    assert client.post("/api/cpm/refresh-request", headers=_auth_headers()).status_code == 503
    assert sent == []

    # Enable Telegram env vars
    monkeypatch.setenv("CPM_ALERT_TELEGRAM_BOT_TOKEN", "bot-token-test")
    monkeypatch.setenv("CPM_ALERT_TELEGRAM_CHAT_ID", "123456")
    monkeypatch.setenv("CPM_ALERT_COOLDOWN_SECONDS", "1800")

    # Offline refresh error -> sends 1 alert
    assert client.post("/api/cpm/refresh-request", headers=_auth_headers()).status_code == 503
    assert len(sent) == 1
    assert "collector-offline" in sent[0][2]

    # Repeated identical error within cooldown -> suppressed (no spam)
    assert client.post("/api/cpm/refresh-request", headers=_auth_headers()).status_code == 503
    assert len(sent) == 1

    # Different error (scheduled 15m failure) -> notifies
    fail = client.post(
        "/api/cpm/collector/failure",
        json={
            "collectorId": "mac-vpn-collector",
            "area": "torna",
            "triggerKind": "scheduled-15m",
            "errorCode": "vpn-closed",
            "errorMessage": "SELSA VPN tüneli kapalı.",
        },
        headers=collector_headers,
    )
    assert fail.status_code == 200
    assert len(sent) == 2
    assert "15 dk otomatik çekim" in sent[1][2]
    assert "vpn-closed" in sent[1][2]

    # Successful snapshot ingest -> sends single recovery message
    ing1 = client.post("/api/cpm/collector/ingest", json=_sample_piston_payload(), headers=collector_headers)
    assert ing1.status_code == 200
    assert len(sent) == 3
    assert "Geri Geldi" in sent[2][2]

    # Next successful ingest -> no duplicate recovery message
    ing2 = client.post(
        "/api/cpm/collector/ingest",
        json=_sample_piston_payload(captured_at="2026-11-26T11:45:00+03:00"),
        headers=collector_headers,
    )
    assert ing2.status_code == 200
    assert len(sent) == 3


def test_payload_validation_rejects_mismatched_raw_material_total_and_duplicate_keys(cpm_env):
    client = TestClient(app)
    collector_headers = {"X-CPM-Collector-Token": "test-collector-secret-token"}

    bad_total = _sample_piston_payload()
    bad_total["rawMaterials"][0]["totalAvailableKg"] = 999.0
    assert client.post("/api/cpm/collector/ingest", json=bad_total, headers=collector_headers).status_code == 422

    dup_prod = _sample_piston_payload()
    dup_prod["productStocks"].append(dict(dup_prod["productStocks"][0]))
    assert client.post("/api/cpm/collector/ingest", json=dup_prod, headers=collector_headers).status_code == 422


def test_cpm_ingest_leaves_operational_planning_database_unchanged_and_rejects_aliasing(cpm_env):
    from app.config import settings

    with pytest.raises(CpmError):
        validate_store_path(settings.database_path)

    client = TestClient(app)
    collector_headers = {"X-CPM-Collector-Token": "test-collector-secret-token"}
    db_file = Path(settings.database_path)
    before_state = client.get("/api/planning-state", headers=_auth_headers()).text
    before_hash = hashlib.sha256(db_file.read_bytes()).hexdigest() if db_file.exists() else None

    assert client.post("/api/cpm/collector/ingest", json=_sample_piston_payload(), headers=collector_headers).status_code == 200
    assert client.get("/api/cpm/piston/latest", headers=_auth_headers()).status_code == 200
    # Offline refresh returns 503 without touching operational DB
    assert client.post("/api/cpm/refresh-request", headers=_auth_headers()).status_code == 503
    # Online refresh returns 200 without touching operational DB
    assert client.post(
        "/api/cpm/collector/heartbeat",
        json={"collectorId": "mac-vpn-collector", "area": "torna", "vpnConnected": True, "intervalSeconds": 900},
        headers=collector_headers,
    ).status_code == 200
    assert client.post("/api/cpm/refresh-request", headers=_auth_headers()).status_code == 200

    after_state = client.get("/api/planning-state", headers=_auth_headers()).text
    assert after_state == before_state
    if before_hash is not None:
        assert hashlib.sha256(db_file.read_bytes()).hexdigest() == before_hash
