"""Authoritative report snapshots. Python formats; the shared TS domain runtime calculates."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from .database import planning_state
from .models import DeliveryPlanPayload

RUNTIME = Path(__file__).resolve().parents[1] / "runtime" / "delivery-runtime.cjs"
MAX_INPUT = 16 * 1024 * 1024
MAX_OUTPUT = 4 * 1024 * 1024
RUNTIME_TIMEOUT = 20


class DeliveryReportError(ValueError):
    def __init__(self, message: str, status: int = 422):
        super().__init__(message)
        self.status = status


def run_delivery_runtime(seed: dict, scope: dict, today: str) -> tuple[dict, str]:
    try:
        manifest = json.loads(RUNTIME.with_suffix(".cjs.json").read_text())
        engine = hashlib.sha256(RUNTIME.read_bytes()).hexdigest()
        if engine != manifest["runtimeSha256"]:
            raise ValueError("runtime mismatch")
    except (OSError, ValueError, KeyError):
        raise DeliveryReportError("Teslimat hesaplama bileşeni hazır değil. Sistem yöneticisine bildirin.", 503)
    data = json.dumps({"seed": seed, "range": scope, "today": today}, ensure_ascii=False, allow_nan=False).encode()
    if len(data) > MAX_INPUT:
        raise DeliveryReportError("Üretim verisi teslimat hesaplama sınırını aşıyor.", 413)
    # Fixed executable/entrypoint; never invoke a shell or inherit Node injection options.
    env = {key: value for key, value in os.environ.items() if key in {"PATH", "SYSTEMROOT"}}
    env["TZ"] = "Europe/Istanbul"
    try:
        with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as errors:
            subprocess.run([os.environ.get("DELIVERY_NODE_BINARY", "node"), "--max-old-space-size=256", str(RUNTIME)], input=data,
                           stdout=output, stderr=errors, timeout=RUNTIME_TIMEOUT, check=True, env=env)
            if output.tell() > MAX_OUTPUT:
                raise DeliveryReportError("Teslimat hesaplama çıktısı sınırı aşıyor.", 503)
            output.seek(0)
            report = json.loads(output.read(MAX_OUTPUT + 1))
    except (OSError, subprocess.SubprocessError, ValueError):
        raise DeliveryReportError("Teslimat hesabı tamamlanamadı. Plan değişmedi; tekrar deneyin.", 503)
    if not isinstance(report, dict) or not isinstance(report.get("error"), str) or type(report.get("complete")) is not bool:
        raise DeliveryReportError("Teslimat hesabı geçersiz çıktı üretti.", 503)
    if report["error"] or report.get("payload") is None:
        raise DeliveryReportError(report["error"] or "Teslimat raporu hesaplanamadı.")
    try:
        report["payload"] = DeliveryPlanPayload.model_validate(report["payload"]).model_dump()
        if not isinstance(report["undated"], list) or type(report["undatedQuantity"]) is not int or report["undatedQuantity"] < 0:
            raise ValueError("invalid completeness")
        if report["complete"] != (len(report["undated"]) == 0):
            raise ValueError("invalid completeness")
    except (ValueError, KeyError, TypeError):
        raise DeliveryReportError("Teslimat hesabı doğrulanamadı.", 503)
    return report, engine


def report_snapshot(expected_revision: str, scope: dict, calculation_date: str | None = None) -> dict:
    state = planning_state()
    if not state or not state.get("seed"):
        raise DeliveryReportError("Önce ortak üretim planını kaydedin.", 409)
    if state["updatedAt"] != expected_revision:
        raise DeliveryReportError("Ortak plan değişti. Güncel veriyi yükleyip teslimat önizlemesini yenileyin.", 409)
    today = datetime.now(ZoneInfo("Europe/Istanbul")).date().isoformat()
    if calculation_date is not None and calculation_date != today:
        raise DeliveryReportError("Hesaplama günü değişti. Teslimat önizlemesini yenileyin.", 409)
    report, engine = run_delivery_runtime(state["seed"], scope, today)
    canonical = json.dumps({"revision": expected_revision, "engine": engine, "today": today, "scope": scope, "report": report}, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    current = planning_state()
    if not current or current["updatedAt"] != expected_revision:
        raise DeliveryReportError("Hesaplama sırasında ortak plan değişti. Önizlemeyi yenileyin.", 409)
    return {"revision": expected_revision, "engineVersion": engine, "calculationDate": today,
            "calculatedAt": datetime.now(timezone.utc).isoformat(), "digest": digest, "report": report}
