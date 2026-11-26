#!/usr/bin/env python3
"""Read-only Piston CPM collector: 15-minute schedule + on-demand UI refresh polling.

Connects to SQL Server SELSA_17 via TLS 1.2 with exact SHA-256 certificate pinning
and posts bounded Piston snapshots to the Planning Automation backend using a
dedicated X-CPM-Collector-Token header. Never writes to SQL Server and never
mutates Planning Automation's operational planning databases.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timedelta
import hashlib
import json
import logging
import os
from pathlib import Path
import ssl
import subprocess
import sys
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

ISTANBUL = ZoneInfo("Europe/Istanbul")
DEFAULT_SQL_SERVER = "192.168.16.111"
DEFAULT_SQL_PORT = 1433
DEFAULT_SQL_DATABASE = "SELSA_17"
DEFAULT_CERT_PIN = "4901cc483d58f14e61dd2f7a932fb1ff2fc6a25f87b2c741d0e70e0cbd5bac51"
DEFAULT_INTERVAL_SECONDS = 900  # 15 minutes
DEFAULT_HEARTBEAT_SECONDS = 15
DEFAULT_COLLECTOR_ID = "mac-vpn-collector"
WORK_ORDER_LOOKBACK_DAYS = 45
MAX_WORK_ORDERS = 1200

EXCLUDED_SCRAP_DEPOTS = frozenset({"ISK", "149"})
STAGE_ORDER = {"010": 1, "040": 2, "060": 3, "160": 4, "290": 5}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [cpm-collector] %(levelname)s %(message)s",
)
logger = logging.getLogger("cpm-collector")


def _load_dotenv_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in {"'", '"'}:
            val = val[1:-1]
        values[key] = val
    return values


def _resolve_runtime_paths(cert_path_arg: str | None, openssl_conf_arg: str | None) -> tuple[Path, Path, Path]:
    workspace_root = Path(__file__).resolve().parents[3]
    fallback_runtime = workspace_root / "work" / "staging-cpm-data-20261115" / "runtime"
    if not fallback_runtime.is_dir():
        fallback_runtime = Path("/Users/furkangok/Developer/planning-automation/work/staging-cpm-data-20261115/runtime")

    cert_path = Path(cert_path_arg or os.getenv("CPM_SQL_CERT_FILE") or (fallback_runtime / "sql-server-observed-cert.pem")).resolve()
    openssl_conf = Path(openssl_conf_arg or os.getenv("CPM_OPENSSL_CONF") or (fallback_runtime / "openssl-cpm-test.cnf")).resolve()
    empty_ca_dir = Path(os.getenv("CPM_EMPTY_CA_DIR") or (fallback_runtime / "empty-ca-dir")).resolve()
    return cert_path, openssl_conf, empty_ca_dir


def _check_vpn_route(sql_host: str) -> bool:
    if sys.platform != "darwin":
        return True
    try:
        output = subprocess.check_output(["/sbin/route", "-n", "get", sql_host], text=True, timeout=5)
    except Exception:
        return False
    return any(line.strip().startswith("interface: ppp") for line in output.splitlines())


def _safe_error(exc: Exception, secrets: tuple[str, ...]) -> str:
    text = f"{type(exc).__name__}: {exc}"
    for secret in secrets:
        if secret:
            text = text.replace(secret, "[redacted]")
    return text[:450]


def _connect_pinned_tds(
    *,
    server: str,
    port: int,
    database: str,
    user: str,
    password: str,
    cert_path: Path,
    openssl_conf: Path,
    empty_ca_dir: Path,
    expected_pin: str,
):
    if not cert_path.is_file():
        raise RuntimeError(f"SQL sertifika dosyası bulunamadı: {cert_path}")
    observed_pin = hashlib.sha256(ssl.PEM_cert_to_DER_cert(cert_path.read_text(encoding="utf-8"))).hexdigest()
    if observed_pin != expected_pin:
        raise RuntimeError("Onaylı SQL sertifika parmak izi uyuşmuyor.")

    os.environ["OPENSSL_CONF"] = str(openssl_conf)
    os.environ["SSL_CERT_FILE"] = str(cert_path)
    os.environ["SSL_CERT_DIR"] = str(empty_ca_dir)

    from OpenSSL import SSL, crypto
    import pytds
    from pytds import tls

    logging.getLogger("pytds").setLevel(logging.CRITICAL)

    def cert_fp(cert) -> str:
        return hashlib.sha256(crypto.dump_certificate(crypto.FILETYPE_ASN1, cert)).hexdigest()

    seen = {"verified": False}

    def verify(_connection, cert, _error_number, depth, ok):
        match = depth == 0 and cert_fp(cert) == expected_pin
        seen["verified"] = bool(ok and match)
        return bool(ok and match)

    def create_ctx(cafile: str):
        if cafile != str(cert_path):
            raise RuntimeError("Beklenmeyen sertifika güven dosyası.")
        ctx = SSL.Context(SSL.TLS_CLIENT_METHOD)
        ctx.set_min_proto_version(SSL.TLS1_2_VERSION)
        ctx.set_max_proto_version(SSL.TLS1_2_VERSION)
        ctx.set_cipher_list(b"ECDHE-RSA-AES256-SHA384:@SECLEVEL=0")
        ctx.load_verify_locations(cafile=cafile)
        ctx.set_verify(SSL.VERIFY_PEER, verify)
        return ctx

    old_ctx, old_host = tls.create_context, tls.validate_host
    tls.create_context = create_ctx
    tls.validate_host = lambda cert, name: cert_fp(cert) == expected_pin
    try:
        conn = pytds.connect(
            server=server,
            port=port,
            database=database,
            user=user,
            password=password,
            cafile=str(cert_path),
            validate_host=True,
            enc_login_only=False,
            readonly=True,
            autocommit=False,
            login_timeout=10,
            timeout=30,
            disable_connect_retry=True,
            appname="PlanningAutomation CPM Piston Collector",
        )
        if not seen["verified"]:
            conn.close()
            raise RuntimeError("SQL sunucu sertifika parmak izi doğrulanamadı.")
        return conn
    finally:
        tls.create_context, tls.validate_host = old_ctx, old_host


def _query(conn, sql: str, params: tuple | None = None) -> list[tuple]:
    with conn.cursor() as cur:
        if params is None:
            cur.execute("SET NOCOUNT ON; " + sql)
        else:
            cur.execute("SET NOCOUNT ON; " + sql, params)
        if not cur.description:
            return []
        return cur.fetchall()


def _f(value: Any) -> float:
    return 0.0 if value is None else float(value)


def _derive_wo_stage(stages: list[dict[str, Any]]) -> str:
    by_wc = {s["workCenterCode"]: s for s in stages}
    s290 = by_wc.get("290")
    s160 = by_wc.get("160")
    s060 = by_wc.get("060")
    s040 = by_wc.get("040")
    s010 = by_wc.get("010")

    if s290 and (s290["opStatus"] == 20 or (s290["producedQty"] > 0 and s290["producedQty"] >= s290["targetQty"] * 0.9)):
        return "gkm-completed"
    if s290 and s290["producedQty"] > 0:
        return "gkm-in-progress"
    if s160 and (s160["opStatus"] == 20 or (s160["producedQty"] > 0 and s160["producedQty"] >= s160["targetQty"] * 0.9)):
        return "gkm-queue"
    if s160 and s160["producedQty"] > 0:
        return "washing-in-progress"
    if s060 and (s060["opStatus"] == 20 or (s060["producedQty"] > 0 and s060["producedQty"] >= s060["targetQty"] * 0.9)):
        return "washing-queue" if s160 else "gkm-queue"
    if s060 and s060["producedQty"] > 0:
        return "deburring-in-progress"
    if s040 and (s040["opStatus"] == 20 or (s040["producedQty"] > 0 and s040["producedQty"] >= s040["targetQty"] * 0.9)):
        return "deburring-queue" if s060 else ("washing-queue" if s160 else "gkm-queue")
    if s040 and s040["producedQty"] > 0:
        return "drilling-in-progress"
    if s010 and (s010["opStatus"] == 20 or (s010["producedQty"] > 0 and s010["producedQty"] >= s010["targetQty"] * 0.9)):
        return "drilling-queue"
    if s010 and s010["producedQty"] > 0:
        return "turning-in-progress"
    return "not-started"


def _fmt_iso_local(dt_val: Any) -> str | None:
    if dt_val is None:
        return None
    if isinstance(dt_val, datetime):
        if dt_val.year < 2000:
            return None
        return dt_val.replace(tzinfo=ISTANBUL).isoformat()
    text = str(dt_val).strip()
    return text or None


def collect_piston_snapshot(
    conn,
    *,
    collector_id: str,
    trigger_kind: str,
    request_id: str | None = None,
) -> dict[str, Any]:
    started_at = datetime.now(ISTANBUL)
    cutoff_date = (started_at - timedelta(days=WORK_ORDER_LOOKBACK_DAYS)).strftime("%Y-%m-%d")

    # 1. Discover all Piston products (SKOD9='320' OR active/recent 320- work orders)
    piston_prod_rows = _query(
        conn,
        """
        SELECT DISTINCT MALKOD FROM (
            SELECT MALKOD FROM dbo.STKKRT WITH (NOLOCK)
            WHERE SIRKETNO='17' AND KAYITDURUM=1 AND MALTIP=0 AND SKOD9='320'
            UNION
            SELECT MAMULKOD AS MALKOD FROM dbo.URTKRT WITH (NOLOCK)
            WHERE SIRKETNO='17' AND EVRAKTIP=54 AND URETIMNO LIKE '320-%' AND EVRAKTARIH >= '2025-01-01'
        ) P
        WHERE ISNULL(MALKOD, '') <> ''
        ORDER BY MALKOD
        """,
    )
    piston_products = [str(r[0]).strip() for r in piston_prod_rows]
    if not piston_products:
        raise RuntimeError("CPM'de Piston ürünü bulunamadı.")
    prod_ph = ",".join(["%s"] * len(piston_products))

    # 2. BOM raw material weights (MAMKRT) for Piston products
    bom_rows = _query(
        conn,
        f"""
        SELECT k.MAMULKOD, k.VERSIYONNO, k.HAMMADDEKOD, ISNULL(s.MALAD, ''), k.MIKTAR, ISNULL(k.HAMMADDEBIRIM, 'GRAM')
        FROM dbo.MAMKRT k WITH (NOLOCK)
        LEFT JOIN dbo.STKKRT s WITH (NOLOCK) ON s.SIRKETNO=k.SIRKETNO AND s.MALKOD=k.HAMMADDEKOD
        WHERE k.SIRKETNO='17' AND k.KAYITDURUM=1
              AND k.MAMULKOD IN ({prod_ph})
              AND k.HAMMADDEKOD <> k.MAMULKOD
        ORDER BY k.MAMULKOD, k.VERSIYONNO
        """,
        tuple(piston_products),
    )
    bom_by_prod: dict[str, dict[str, Any]] = {}
    rm_codes_set: set[str] = set()
    for malkod, _ver, hm, hmad, mik, brm in bom_rows:
        prod = str(malkod).strip()
        hm_code = str(hm).strip()
        if not hm_code:
            continue
        unit = str(brm).strip().upper() or "GRAM"
        raw_qty = _f(mik)
        grams = round(raw_qty * 1000.0, 4) if unit == "KG" else round(raw_qty, 4)
        if prod not in bom_by_prod or hm_code.startswith("Z"):
            bom_by_prod[prod] = {
                "product": prod,
                "materialCode": hm_code,
                "materialName": str(hmad).strip(),
                "grams": grams,
                "unit": "GRAM",
            }
        if hm_code.startswith("Z"):
            rm_codes_set.add(hm_code)
    bom_weights = [bom_by_prod[p] for p in sorted(bom_by_prod)]

    # 3. Raw Material Stocks (VW_STKDRM WITH NOEXPAND) -> 141 + 320 primary scope
    raw_materials: list[dict[str, Any]] = []
    rm_codes = sorted(rm_codes_set)
    if rm_codes:
        rm_ph = ",".join(["%s"] * len(rm_codes))
        rm_rows = _query(
            conn,
            f"""
            SELECT v.MALKOD, ISNULL(s.MALAD, ''), ISNULL(s.BIRIM, 'KG'), v.DEPOKOD, ISNULL(d.DEPOAD, ''),
                   SUM(v.STOKGIRIS - v.STOKCIKIS) AS STOKMIKTAR
            FROM dbo.VW_STKDRM v WITH (NOEXPAND, NOLOCK)
            LEFT JOIN dbo.STKKRT s WITH (NOLOCK) ON s.SIRKETNO=v.SIRKETNO AND s.MALKOD=v.MALKOD
            LEFT JOIN dbo.DEPKRT d WITH (NOLOCK) ON d.SIRKETNO=v.SIRKETNO AND d.DEPOKOD=v.DEPOKOD
            WHERE v.SIRKETNO='17' AND v.MALKOD IN ({rm_ph})
            GROUP BY v.MALKOD, s.MALAD, s.BIRIM, v.DEPOKOD, d.DEPOAD
            HAVING SUM(v.STOKGIRIS - v.STOKCIKIS) <> 0
            ORDER BY v.MALKOD, v.DEPOKOD
            """,
            tuple(rm_codes),
        )
        rm_acc: dict[str, dict[str, Any]] = {}
        for code in rm_codes:
            rm_acc[code] = {
                "materialCode": code,
                "materialName": "",
                "unit": "KG",
                "depot141Kg": 0.0,
                "depot320Kg": 0.0,
                "depot250Kg": 0.0,
                "depot960Kg": 0.0,
                "otherDepots": [],
            }
        for code, name, unit, depo, depoad, qty in rm_rows:
            code_s = str(code).strip()
            depo_s = str(depo).strip()
            if depo_s in EXCLUDED_SCRAP_DEPOTS:
                continue
            q_val = round(_f(qty), 4)
            rec = rm_acc[code_s]
            if not rec["materialName"]:
                rec["materialName"] = str(name).strip()
            rec["unit"] = str(unit).strip() or "KG"
            if depo_s == "141":
                rec["depot141Kg"] = round(rec["depot141Kg"] + q_val, 4)
            elif depo_s == "320":
                rec["depot320Kg"] = round(rec["depot320Kg"] + q_val, 4)
            elif depo_s == "250":
                rec["depot250Kg"] = round(rec["depot250Kg"] + q_val, 4)
            elif depo_s == "960":
                rec["depot960Kg"] = round(rec["depot960Kg"] + q_val, 4)
            else:
                rec["otherDepots"].append({"depotCode": depo_s, "depotName": str(depoad).strip(), "kg": q_val})
        for code in rm_codes:
            rec = rm_acc[code]
            rec["totalAvailableKg"] = round(rec["depot141Kg"] + rec["depot320Kg"], 4)
            raw_materials.append(rec)

    # 4. Piston Product WIP & Finished Stocks (VW_STKDRM WITH NOEXPAND)
    stk_rows = _query(
        conn,
        f"""
        SELECT v.MALKOD, v.DEPOKOD, ISNULL(d.DEPOAD, ''), ISNULL(v.VERSIYONNO, ''),
               SUM(v.STOKGIRIS - v.STOKCIKIS) AS STOKMIKTAR
        FROM dbo.VW_STKDRM v WITH (NOEXPAND, NOLOCK)
        LEFT JOIN dbo.DEPKRT d WITH (NOLOCK) ON d.SIRKETNO=v.SIRKETNO AND d.DEPOKOD=v.DEPOKOD
        WHERE v.SIRKETNO='17' AND v.MALKOD IN ({prod_ph})
        GROUP BY v.MALKOD, v.DEPOKOD, d.DEPOAD, v.VERSIYONNO
        HAVING SUM(v.STOKGIRIS - v.STOKCIKIS) <> 0
        ORDER BY v.MALKOD, v.DEPOKOD, v.VERSIYONNO
        """,
        tuple(piston_products),
    )
    stk_acc: dict[str, dict[str, Any]] = {}
    for prod in piston_products:
        stk_acc[prod] = {
            "product": prod,
            "drillingQueueQty": 0.0,
            "deburringQueueQty": 0.0,
            "gkmQueueQty": 0.0,
            "gkmCompletedQty": 0.0,
            "finishedWarehouseQty": 0.0,
            "consignmentQty": 0.0,
            "scrapExcludedQty": 0.0,
            "depots": [],
        }
    for malkod, depo, depoad, ver, qty in stk_rows:
        prod = str(malkod).strip()
        depo_s = str(depo).strip()
        ver_s = str(ver).strip()
        q_val = round(_f(qty), 4)
        rec = stk_acc[prod]
        if depo_s in EXCLUDED_SCRAP_DEPOTS:
            if q_val > 0:
                rec["scrapExcludedQty"] = round(rec["scrapExcludedQty"] + q_val, 4)
            continue
        if q_val <= 0:
            continue
        rec["depots"].append({"depotCode": depo_s, "depotName": str(depoad).strip(), "version": ver_s, "qty": q_val})
        if depo_s == "320" and ver_s == "010":
            rec["drillingQueueQty"] = round(rec["drillingQueueQty"] + q_val, 4)
        elif depo_s == "320" and ver_s == "040":
            rec["deburringQueueQty"] = round(rec["deburringQueueQty"] + q_val, 4)
        elif depo_s == "196" and ver_s == "160":
            rec["gkmQueueQty"] = round(rec["gkmQueueQty"] + q_val, 4)
        elif depo_s == "196" and ver_s == "":
            rec["gkmCompletedQty"] = round(rec["gkmCompletedQty"] + q_val, 4)
        elif depo_s == "145":
            rec["finishedWarehouseQty"] = round(rec["finishedWarehouseQty"] + q_val, 4)
        elif depo_s == "800":
            rec["consignmentQty"] = round(rec["consignmentQty"] + q_val, 4)

    product_stocks = [
        stk_acc[p]
        for p in piston_products
        if stk_acc[p]["depots"] or stk_acc[p]["scrapExcludedQty"] > 0
    ]

    # 5. Active & recent Piston Work Orders (URTKRT + URTROT + latest URTRKO per stage)
    wo_header_rows = _query(
        conn,
        f"""
        SELECT TOP {MAX_WORK_ORDERS} URETIMNO, MAX(MAMULKOD) AS MAMULKOD,
               MAX(MIKTAR) AS MIKTAR, MAX(EVRAKTARIH) AS EVRAKTARIH, MIN(URETIMDURUM) AS MIN_DURUM
        FROM dbo.URTKRT WITH (NOLOCK)
        WHERE SIRKETNO='17' AND EVRAKTIP=54 AND URETIMNO LIKE '320-%%'
              AND (URETIMDURUM IN (0, 1, 2) OR EVRAKTARIH >= %s)
        GROUP BY URETIMNO
        ORDER BY MAX(EVRAKTARIH) DESC, URETIMNO DESC
        """,
        (cutoff_date,),
    )
    wo_ids = [str(r[0]).strip() for r in wo_header_rows if str(r[0]).strip()]
    wo_meta = {
        str(r[0]).strip(): {
            "uretimNo": str(r[0]).strip(),
            "product": str(r[1]).strip(),
            "targetQty": round(_f(r[2]), 4),
            "orderDate": str(r[3])[:10] if r[3] else "",
            "orderStatus": int(r[4] or 0),
        }
        for r in wo_header_rows
        if str(r[0]).strip()
    }

    stages_by_wo: dict[str, list[dict[str, Any]]] = defaultdict(list)
    if wo_ids:
        # Query in bounded chunks to stay well under SQL Server parameter limits
        for start in range(0, len(wo_ids), 250):
            chunk = wo_ids[start : start + 250]
            wph = ",".join(["%s"] * len(chunk))
            stage_rows = _query(
                conn,
                f"""
                WITH LatestRuns AS (
                    SELECT EVRAKNO, OPERASYONNO, KAYNAKKOD, BITTARIH, BITTARIHSAAT, VARDIYAKOD,
                           ROW_NUMBER() OVER (
                               PARTITION BY EVRAKNO, OPERASYONNO
                               ORDER BY BITTARIH DESC, BITTARIHSAAT DESC, ID DESC
                           ) AS rn
                    FROM dbo.URTRKO WITH (NOLOCK)
                    WHERE SIRKETNO='17' AND EVRAKTIP=54 AND URETIMNO IN ({wph})
                )
                SELECT k.URETIMNO, k.EVRAKNO, ISNULL(k.VERSIYONNO, ''), k.MIKTAR,
                       r.OPERASYONNO, ISNULL(r.ISMERKEZKOD, ''), ISNULL(r.ACIKLAMA, ''),
                       ISNULL(r.OPMIKTAR, 0), ISNULL(r.OPFIREMIKTAR, 0), ISNULL(r.OPDURUM, 0),
                       lr.KAYNAKKOD, ISNULL(u.KAYNAKAD, ''), ISNULL(u.LKOD1, ''),
                       lr.BITTARIH, lr.BITTARIHSAAT, lr.VARDIYAKOD
                FROM dbo.URTKRT k WITH (NOLOCK)
                JOIN dbo.URTROT r WITH (NOLOCK)
                  ON r.SIRKETNO=k.SIRKETNO AND r.EVRAKTIP=k.EVRAKTIP AND r.EVRAKNO=k.EVRAKNO
                LEFT JOIN LatestRuns lr
                  ON lr.EVRAKNO=k.EVRAKNO AND lr.OPERASYONNO=r.OPERASYONNO AND lr.rn=1
                LEFT JOIN dbo.URTKYN u WITH (NOLOCK)
                  ON u.SIRKETNO=k.SIRKETNO AND u.KAYNAKKOD=lr.KAYNAKKOD
                WHERE k.SIRKETNO='17' AND k.EVRAKTIP=54 AND k.URETIMNO IN ({wph})
                """,
                tuple(chunk) + tuple(chunk),
            )
            for row in stage_rows:
                uo = str(row[0]).strip()
                wc = str(row[5]).strip()
                if not wc:
                    continue
                # Combine BITTARIH date + BITTARIHSAAT time if both present
                run_dt = None
                if isinstance(row[13], datetime) and row[13].year >= 2000:
                    if isinstance(row[14], datetime):
                        run_dt = row[13].replace(hour=row[14].hour, minute=row[14].minute, second=row[14].second)
                    else:
                        run_dt = row[13]
                stages_by_wo[uo].append(
                    {
                        "isemriNo": str(row[1]).strip(),
                        "version": str(row[2]).strip(),
                        "workCenterCode": wc,
                        "workCenterName": str(row[6]).strip(),
                        "targetQty": max(0.0, round(_f(row[3]), 4)),
                        "producedQty": max(0.0, round(_f(row[7]), 4)),
                        "scrapQty": max(0.0, round(_f(row[8]), 4)),
                        "opStatus": int(row[9] or 0),
                        "lastMachineCode": str(row[10]).strip() if row[10] else None,
                        "lastMachineName": str(row[11]).strip() if row[11] else None,
                        "lastErpCode": str(row[12]).strip() if row[12] else None,
                        "lastRunAt": _fmt_iso_local(run_dt),
                        "lastShift": str(row[15]).strip() if row[15] else None,
                    }
                )

    work_orders: list[dict[str, Any]] = []
    for uo in wo_ids:
        meta = wo_meta[uo]
        stages = sorted(
            stages_by_wo.get(uo, []),
            key=lambda s: (STAGE_ORDER.get(s["workCenterCode"], 99), s["isemriNo"]),
        )
        if not stages:
            continue
        turning = next((s for s in stages if s["workCenterCode"] == "010"), None)
        work_orders.append(
            {
                **meta,
                "currentStage": _derive_wo_stage(stages),
                "turningMachineCode": turning["lastMachineCode"] if turning else None,
                "turningMachineName": turning["lastMachineName"] if turning else None,
                "turningErpCode": turning["lastErpCode"] if turning else None,
                "turningProducedQty": turning["producedQty"] if turning else 0.0,
                "turningLastRunAt": turning["lastRunAt"] if turning else None,
                "stages": stages,
            }
        )

    # 6. Cycle times (MAMKYN.NKOD1) & resources (URTKYN) for Piston products
    cycle_rows = _query(
        conn,
        f"""
        SELECT k.MAMULKOD, ISNULL(k.VERSIYONNO, ''), k.ISMERKEZKOD, k.KAYNAKKOD,
               ISNULL(u.KAYNAKAD, ''), ISNULL(u.LKOD1, ''), MAX(ISNULL(k.NKOD1, 0)) AS SURE
        FROM dbo.MAMKYN k WITH (NOLOCK)
        LEFT JOIN dbo.URTKYN u WITH (NOLOCK) ON u.SIRKETNO=k.SIRKETNO AND u.KAYNAKKOD=k.KAYNAKKOD
        WHERE k.SIRKETNO='17' AND k.KAYITDURUM=1 AND k.MAMULKOD IN ({prod_ph}) AND ISNULL(k.NKOD1, 0) > 0
        GROUP BY k.MAMULKOD, k.VERSIYONNO, k.ISMERKEZKOD, k.KAYNAKKOD, u.KAYNAKAD, u.LKOD1
        ORDER BY k.MAMULKOD, k.ISMERKEZKOD, k.KAYNAKKOD
        """,
        tuple(piston_products),
    )
    cycle_times = []
    res_map: dict[str, dict[str, Any]] = {}
    for prod, ver, wc, rk, rname, lkod1, sure in cycle_rows:
        rk_s = str(rk).strip()
        erp_s = str(lkod1).strip()
        rname_s = str(rname).strip()
        cycle_times.append(
            {
                "product": str(prod).strip(),
                "version": str(ver).strip(),
                "workCenterCode": str(wc).strip(),
                "resourceCode": rk_s,
                "resourceName": rname_s,
                "erpWorkCenterCode": erp_s,
                "cycleSeconds": round(_f(sure), 4),
            }
        )
        if rk_s not in res_map:
            res_map[rk_s] = {
                "resourceCode": rk_s,
                "resourceName": rname_s,
                "erpWorkCenterCode": erp_s,
                "active": True,
            }

    finished_at = datetime.now(ISTANBUL)
    return {
        "schemaVersion": 1,
        "area": "torna",
        "company": "17",
        "collectorId": collector_id,
        "triggerKind": trigger_kind,
        "requestId": request_id,
        "startedAt": started_at.isoformat(),
        "capturedAt": finished_at.isoformat(),
        "rawMaterialScope": "141+320",
        "rawMaterials": raw_materials,
        "productStocks": product_stocks,
        "workOrders": work_orders,
        "parameters": {
            "bomWeights": bom_weights,
            "cycleTimes": cycle_times,
            "resources": [res_map[k] for k in sorted(res_map)],
        },
    }


def _http_post_json(url: str, token: str, payload: dict[str, Any], timeout: int = 30) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-CPM-Collector-Token": token,
            "X-Production-Area": "torna",
        },
    )
    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _save_pending_queue(queue_file: Path, payload: dict[str, Any]) -> None:
    queue_file.parent.mkdir(parents=True, exist_ok=True)
    tmp = queue_file.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    os.chmod(tmp, 0o600)
    tmp.replace(queue_file)


def _flush_pending_queue(queue_file: Path, api_url: str, token: str) -> None:
    if not queue_file.is_file():
        return
    try:
        payload = json.loads(queue_file.read_text(encoding="utf-8"))
        res = _http_post_json(f"{api_url}/cpm/collector/ingest", token, payload)
        queue_file.unlink(missing_ok=True)
        logger.info("Kuyruktaki CPM snapshot yüklendi: snapshotId=%s", res.get("snapshotId"))
    except Exception as exc:
        logger.warning("Kuyruktaki snapshot gönderilemedi (sonraki döngüde tekrar denenecek): %s", exc)


def run_once(
    *,
    args: argparse.Namespace,
    sql_user: str,
    sql_password: str,
    collector_token: str,
    cert_path: Path,
    openssl_conf: Path,
    empty_ca_dir: Path,
    trigger_kind: str,
    request_id: str | None = None,
) -> bool:
    if not args.skip_vpn_check and not _check_vpn_route(args.sql_server):
        msg = "SELSA VPN tüneli (ppp) kapalı olduğu için CPM okunamadı."
        logger.warning(msg)
        if args.api_url and collector_token:
            try:
                _http_post_json(
                    f"{args.api_url}/cpm/collector/failure",
                    collector_token,
                    {
                        "collectorId": args.collector_id,
                        "area": "torna",
                        "triggerKind": trigger_kind,
                        "requestId": request_id,
                        "errorCode": "vpn-closed",
                        "errorMessage": msg,
                    },
                )
            except Exception as exc:
                logger.warning("Hata bildirimi gönderilemedi: %s", exc)
        return False

    try:
        conn = _connect_pinned_tds(
            server=args.sql_server,
            port=args.sql_port,
            database=args.sql_database,
            user=sql_user,
            password=sql_password,
            cert_path=cert_path,
            openssl_conf=openssl_conf,
            empty_ca_dir=empty_ca_dir,
            expected_pin=args.cert_pin,
        )
        try:
            payload = collect_piston_snapshot(
                conn,
                collector_id=args.collector_id,
                trigger_kind=trigger_kind,
                request_id=request_id,
            )
        finally:
            conn.close()
    except Exception as exc:
        safe_msg = _safe_error(exc, (sql_user, sql_password, collector_token))
        logger.error("CPM SQL okuması başarısız: %s", safe_msg)
        if args.api_url and collector_token:
            try:
                _http_post_json(
                    f"{args.api_url}/cpm/collector/failure",
                    collector_token,
                    {
                        "collectorId": args.collector_id,
                        "area": "torna",
                        "triggerKind": trigger_kind,
                        "requestId": request_id,
                        "errorCode": "sql-read-failed",
                        "errorMessage": safe_msg,
                    },
                )
            except Exception as report_exc:
                logger.warning("SQL hata bildirimi gönderilemedi: %s", report_exc)
        return False

    if args.output_json:
        out_path = Path(args.output_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        os.chmod(out_path, 0o600)
        logger.info(
            "Yerel snapshot yazıldı: %s (hammadde=%d, ürün=%d, işEmri=%d, çevrim=%d)",
            out_path,
            len(payload["rawMaterials"]),
            len(payload["productStocks"]),
            len(payload["workOrders"]),
            len(payload["parameters"]["cycleTimes"]),
        )

    if args.api_url:
        try:
            res = _http_post_json(f"{args.api_url}/cpm/collector/ingest", collector_token, payload)
            logger.info(
                "CPM snapshot yüklendi (%s): snapshotId=%s deduplicated=%s counts=%s",
                trigger_kind,
                res.get("snapshotId"),
                res.get("deduplicated"),
                res.get("counts"),
            )
            return True
        except (HTTPError, URLError, Exception) as exc:
            safe_msg = _safe_error(exc, (sql_user, sql_password, collector_token))
            logger.error("Snapshot yüklemesi başarısız (yerel kuyruğa alındı): %s", safe_msg)
            _save_pending_queue(Path(args.queue_file), payload)
            return False

    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Piston CPM Collector (15m schedule + on-demand)")
    parser.add_argument("--api-url", default=os.getenv("CPM_API_URL", "").rstrip("/"), help="Target API base URL ending with /api")
    parser.add_argument("--collector-id", default=os.getenv("CPM_COLLECTOR_ID", DEFAULT_COLLECTOR_ID))
    parser.add_argument("--env-file", default=os.getenv("CPM_ENV_FILE", "/Users/furkangok/Developer/planning-automation/backend/.env"))
    parser.add_argument("--sql-server", default=os.getenv("CPM_SQL_SERVER", DEFAULT_SQL_SERVER))
    parser.add_argument("--sql-port", type=int, default=int(os.getenv("CPM_SQL_PORT", str(DEFAULT_SQL_PORT))))
    parser.add_argument("--sql-database", default=os.getenv("CPM_SQL_DATABASE", DEFAULT_SQL_DATABASE))
    parser.add_argument("--cert-file", default=None)
    parser.add_argument("--openssl-conf", default=None)
    parser.add_argument("--cert-pin", default=os.getenv("CPM_SQL_CERT_PIN", DEFAULT_CERT_PIN))
    parser.add_argument("--interval-seconds", type=int, default=int(os.getenv("CPM_REFRESH_INTERVAL_SECONDS", str(DEFAULT_INTERVAL_SECONDS))))
    parser.add_argument("--heartbeat-seconds", type=int, default=DEFAULT_HEARTBEAT_SECONDS)
    parser.add_argument("--queue-file", default=os.getenv("CPM_QUEUE_FILE", str(Path.home() / ".selsa-cpm-collector-queue.json")))
    parser.add_argument("--output-json", default="", help="Optional private file path to write collected JSON")
    parser.add_argument("--skip-vpn-check", action="store_true", help="Skip macOS ppp route check (for internal LAN hosts)")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--once", action="store_true", help="Collect once and exit")
    mode.add_argument("--daemon", action="store_true", help="Run continuously (15m auto + on-demand polling)")
    args = parser.parse_args()

    dotenv_vals = _load_dotenv_file(Path(args.env_file))
    sql_user = os.getenv("SELSA_CPM_USER_NAME") or dotenv_vals.get("SELSA_CPM_USER_NAME", "")
    sql_password = os.getenv("SELSA_CPM_PASSWORD") or dotenv_vals.get("SELSA_CPM_PASSWORD", "")
    collector_token = os.getenv("CPM_COLLECTOR_TOKEN") or dotenv_vals.get("CPM_COLLECTOR_TOKEN", "")
    if not sql_user or not sql_password:
        logger.error("SELSA_CPM_USER_NAME ve SELSA_CPM_PASSWORD tanımlı olmalıdır.")
        return 2
    if args.api_url and not collector_token:
        logger.error("--api-url kullanıldığında CPM_COLLECTOR_TOKEN tanımlı olmalıdır.")
        return 2

    cert_path, openssl_conf, empty_ca_dir = _resolve_runtime_paths(args.cert_file, args.openssl_conf)

    if args.once:
        ok = run_once(
            args=args,
            sql_user=sql_user,
            sql_password=sql_password,
            collector_token=collector_token,
            cert_path=cert_path,
            openssl_conf=openssl_conf,
            empty_ca_dir=empty_ca_dir,
            trigger_kind="manual",
        )
        return 0 if ok else 1

    # Daemon mode: 15-minute schedule + 15-second heartbeat/on-demand polling
    if not args.api_url:
        logger.error("--daemon modu için --api-url zorunludur.")
        return 2

    interval = max(60, args.interval_seconds)
    hb_interval = max(5, args.heartbeat_seconds)
    queue_file = Path(args.queue_file)
    next_run_mono = 0.0  # run immediately on startup when VPN is open
    last_error: str | None = None

    logger.info(
        "CPM collector başlatıldı: collectorId=%s api=%s interval=%ds heartbeat=%ds",
        args.collector_id,
        args.api_url,
        interval,
        hb_interval,
    )
    while True:
        vpn_ok = args.skip_vpn_check or _check_vpn_route(args.sql_server)
        now_mono = time.monotonic()
        next_sched_dt = datetime.now(ISTANBUL) + timedelta(seconds=max(0, int(next_run_mono - now_mono)))

        _flush_pending_queue(queue_file, args.api_url, collector_token)

        pending_req = None
        try:
            hb_res = _http_post_json(
                f"{args.api_url}/cpm/collector/heartbeat",
                collector_token,
                {
                    "collectorId": args.collector_id,
                    "area": "torna",
                    "vpnConnected": vpn_ok,
                    "intervalSeconds": interval,
                    "nextScheduledAt": next_sched_dt.isoformat(),
                    "lastError": last_error,
                },
                timeout=15,
            )
            pending_req = hb_res.get("pendingRequest")
            server_interval = hb_res.get("refreshIntervalSeconds")
            if isinstance(server_interval, int) and server_interval >= 60:
                interval = server_interval
        except Exception as exc:
            logger.warning("Heartbeat başarısız: %s", _safe_error(exc, (sql_user, sql_password, collector_token)))

        if pending_req and vpn_ok:
            req_id = pending_req.get("requestId")
            logger.info("On-demand CPM yenileme isteği alındı: requestId=%s", req_id)
            ok = run_once(
                args=args,
                sql_user=sql_user,
                sql_password=sql_password,
                collector_token=collector_token,
                cert_path=cert_path,
                openssl_conf=openssl_conf,
                empty_ca_dir=empty_ca_dir,
                trigger_kind="on-demand",
                request_id=req_id,
            )
            last_error = None if ok else "On-demand CPM okuması başarısız."
            if ok:
                next_run_mono = time.monotonic() + interval
        elif now_mono >= next_run_mono:
            if vpn_ok:
                ok = run_once(
                    args=args,
                    sql_user=sql_user,
                    sql_password=sql_password,
                    collector_token=collector_token,
                    cert_path=cert_path,
                    openssl_conf=openssl_conf,
                    empty_ca_dir=empty_ca_dir,
                    trigger_kind="scheduled-15m",
                )
                last_error = None if ok else "Planlı 15 dk CPM okuması başarısız."
            else:
                last_error = "SELSA VPN tüneli kapalı."
                logger.info("Planlı okuma atlandı: VPN kapalı.")
            next_run_mono = time.monotonic() + interval

        time.sleep(hb_interval)


if __name__ == "__main__":
    raise SystemExit(main())
