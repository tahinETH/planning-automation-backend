"""Readable scenario plans for the scenario workbook (T17).

Dates come from the server's stored scenario records and the shared TS route
engine (backend/runtime/scenario-plan-runtime.cjs). The browser's export data
only names the scenarios; its dates are never presented as verified.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

RUNTIME = Path(__file__).resolve().parents[1] / "runtime" / "scenario-plan-runtime.cjs"
MAX_SCENARIOS = 50
MAX_INPUT = 32 * 1024 * 1024
MAX_OUTPUT = 16 * 1024 * 1024
RUNTIME_TIMEOUT = 30


class ScenarioPlanError(ValueError):
    pass


def _run(records: list[dict[str, Any]]) -> tuple[dict[str, Any], str]:
    try:
        manifest = json.loads(RUNTIME.with_suffix(".cjs.json").read_text())
        engine = hashlib.sha256(RUNTIME.read_bytes()).hexdigest()
        if engine != manifest["runtimeSha256"]:
            raise ValueError("runtime mismatch")
    except (OSError, ValueError, KeyError):
        raise ScenarioPlanError("Senaryo plan hesaplama bileşeni hazır değil.")
    try:
        data = json.dumps({"scenarios": records}, ensure_ascii=False, allow_nan=False).encode()
    except (ValueError, TypeError) as error:
        raise ScenarioPlanError("Kayıtlı senaryo geçersiz sayısal veri içeriyor; plan hesaplanmadı.") from error
    if len(data) > MAX_INPUT:
        raise ScenarioPlanError("Seçilen senaryolar plan hesaplama sınırını aşıyor.")
    # Fixed executable/entrypoint; no shell, no inherited Node options.
    env = {key: value for key, value in os.environ.items() if key in {"PATH", "SYSTEMROOT"}}
    env["TZ"] = "Europe/Istanbul"
    try:
        with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as errors:
            subprocess.run([os.environ.get("DELIVERY_NODE_BINARY", "node"), "--max-old-space-size=512", str(RUNTIME)], input=data,
                           stdout=output, stderr=errors, timeout=RUNTIME_TIMEOUT, check=True, env=env)
            if output.tell() > MAX_OUTPUT:
                raise ScenarioPlanError("Senaryo plan çıktısı sınırı aşıyor.")
            output.seek(0)
            result = json.loads(output.read(MAX_OUTPUT + 1))
    except (OSError, subprocess.SubprocessError, ValueError):
        raise ScenarioPlanError("Senaryo planları hesaplanamadı.")
    if not isinstance(result, dict) or result.get("version") != 1 or not isinstance(result.get("scenarios"), list) or result.get("error"):
        raise ScenarioPlanError(str(result.get("error")) if isinstance(result, dict) and result.get("error") else "Senaryo plan çıktısı geçersiz.")
    expected_ids = [record.get("id") for record in records]
    if [item.get("id") if isinstance(item, dict) else None for item in result["scenarios"]] != expected_ids or not all(map(_valid_plan, result["scenarios"])):
        raise ScenarioPlanError("Senaryo plan çıktısı doğrulanamadı.")
    return result, engine


def _valid_plan(item: Any) -> bool:
    """Shape check of one runtime result; anything else is rejected, not shown."""
    if not isinstance(item, dict) or item.get("status") not in ("ok", "invalid") or not isinstance(item.get("warnings"), list):
        return False
    rows = item.get("rows")
    if not isinstance(rows, dict) or set(rows) != {"turning", "drilling", "deburring", "gkm"}:
        return False
    for values in rows.values():
        if not isinstance(values, list) or not all(isinstance(row, dict) and isinstance(row.get("quantity"), (int, float)) and not isinstance(row.get("quantity"), bool) for row in values):
            return False
        for row in values:
            if not math.isfinite(row["quantity"]) or row["quantity"] < 0:
                return False
            for key in ("start", "end", "readyAt"):
                value = row.get(key)
                if value is not None and (not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or not 0 < value < 2_958_466):
                    return False
            setup = row.get("setupHours")
            if setup is not None and (not isinstance(setup, (int, float)) or isinstance(setup, bool) or not math.isfinite(setup) or setup < 0):
                return False
    return all(isinstance(warning, dict) for warning in item["warnings"])


def scenario_plans(requested: list[dict[str, Any]], load: Any) -> dict[str, Any]:
    """Plans for the requested scenarios, computed from stored records only.

    `requested` is the client export list (id/name used only to find records);
    `load(id)` returns the stored record or None. Never raises: failures become
    explicit per-scenario or global messages for the workbook.
    """
    computed_at = datetime.now(timezone.utc).isoformat()
    plans: dict[str, Any] = {"computedAt": computed_at, "engine": None, "error": None, "scenarios": []}
    ids: list[str] = []
    for item in requested[:MAX_SCENARIOS] if isinstance(requested, list) else []:
        identifier = item.get("id") if isinstance(item, dict) else None
        if isinstance(identifier, str) and identifier.strip() and identifier not in ids:
            ids.append(identifier)
    if isinstance(requested, list) and len(requested) > MAX_SCENARIOS:
        plans["error"] = f"En çok {MAX_SCENARIOS} senaryonun planı hesaplandı; diğerleri plan sayfalarında yok."
    stored: list[dict[str, Any]] = []
    for identifier in ids:
        try:
            record = load(identifier)
        except Exception:
            record = None
        if not isinstance(record, dict) or not isinstance(record.get("seed"), dict) or not isinstance(record.get("result"), dict):
            plans["scenarios"].append({"id": identifier, "name": next((str(item.get("name", "")) for item in requested if isinstance(item, dict) and item.get("id") == identifier), ""),
                                       "createdAt": "", "status": "not-stored", "error": "Sunucuda kayıtlı değil; plan hesaplanmadı.",
                                       "rows": {"turning": [], "drilling": [], "deburring": [], "gkm": []}, "warnings": []})
            continue
        stored.append({"id": record.get("id", identifier), "name": record.get("name", ""), "createdAt": record.get("createdAt", ""),
                       "seed": record["seed"], "result": record["result"]})
    if stored:
        try:
            result, engine = _run(stored)
            plans["engine"] = engine
            plans["scenarios"].extend(result["scenarios"])
        except ScenarioPlanError as error:
            plans["error"] = str(error)
            for record in stored:
                plans["scenarios"].append({"id": record["id"], "name": record["name"], "createdAt": record["createdAt"], "status": "invalid",
                                           "error": f"Plan hesaplanamadı: {error}", "rows": {"turning": [], "drilling": [], "deburring": [], "gkm": []}, "warnings": []})
    order = {identifier: index for index, identifier in enumerate(ids)}
    plans["scenarios"].sort(key=lambda item: order.get(item.get("id"), len(order)))
    return plans
