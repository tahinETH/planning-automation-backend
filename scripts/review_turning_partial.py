"""Review a specific Torna split using the shared domain engine; optional revision/digest-checked apply.

No database initialization or migrations. Preview prints only the affected queue and
report summary. Run on the host holding the database; never export the full seed.
Code deployment and applying a production correction require release authorization.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]


def read_state(database: Path):
    with sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True) as db:
        db.execute("PRAGMA query_only=ON")
        db.execute("BEGIN")
        row = db.execute("SELECT seed_json, updated_at FROM planning_state WHERE state_key='default'").fetchone()
        db.rollback()
    if not row:
        raise ValueError("Ortak kayıt bulunamadı.")
    return json.loads(row[0]), row[1]


def prepare(database: Path, node: str, target: dict, scope: dict):
    seed, revision = read_state(database)
    runtime = ROOT / "runtime/turning-partial-repair-runtime.cjs"
    engine = hashlib.sha256(runtime.read_bytes()).hexdigest()
    if json.loads(runtime.with_suffix('.cjs.json').read_text())["runtimeSha256"] != engine:
        raise ValueError("Düzeltme hesaplama sürümü doğrulanamadı.")
    today = datetime.now(ZoneInfo("Europe/Istanbul")).date().isoformat()
    env = {k: v for k, v in os.environ.items() if k in {"PATH", "SYSTEMROOT"}}
    env["TZ"] = "Europe/Istanbul"
    result = subprocess.run([node, "--max-old-space-size=256", str(runtime)],
        input=json.dumps({"seed": seed, "target": target, "range": scope, "today": today}),
        capture_output=True, text=True, timeout=30, env=env)
    proposal = json.loads(result.stdout)
    if result.returncode or proposal.get("error"):
        raise ValueError(proposal.get("error") or "Düzeltme hesaplanamadı.")
    # Hash the full candidate and original: repeated preview/apply cannot ignore intervening edits.
    canonical = json.dumps([revision, engine, today, target, scope, seed, proposal], sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    return seed, proposal["seed"], {"revision": revision, "digest": digest, "engine": engine, "summary": proposal["summary"]}


def apply_proposal(database: Path, original: dict, proposed: dict, review: dict, *, expected_revision: str, expected_digest: str, actor: str, reason: str):
    if not actor.strip() or not reason.strip() or review["revision"] != expected_revision or review["digest"] != expected_digest:
        raise ValueError("Güncel inceleme sürümü, doğrulama kodu, uygulayan kişi ve neden gereklidir.")
    # Import only after the explicit apply checks, and point the existing transaction at this DB.
    sys.path.insert(0, str(ROOT))
    from app import database as db_module
    from types import SimpleNamespace
    prior_settings = db_module.settings
    db_module.settings = SimpleNamespace(database_path=database)
    try:
        state = db_module.planning_state()
        if not state or state["updatedAt"] != expected_revision or state["seed"] != original:
            raise ValueError("Ortak kayıt değişti. Düzeltmeyi yeniden inceleyin.")
        proposed = json.loads(json.dumps(proposed))
        proposed["planningEvents"] = [{"id": f"partial-review-{expected_digest}", "type": "current-job",
            "machineId": review["summary"]["machineId"], "createdAt": datetime.now(timezone.utc).isoformat(),
            "message": f'{review["summary"]["workOrder"]}: kısmi üretim aktarımı doğrulandı; kalan iş ilk sıraya alındı. {reason.strip()} · {actor.strip()}'}, *proposed.get("planningEvents", [])][:200]
        # Existing optimistic transaction includes order dates and archive bookkeeping, with rollback on failure.
        return db_module.save_planning_state(proposed, expected_updated_at=expected_revision, mode="operational",
            actor_id="maintenance-reviewed-partial", actor_name=actor.strip(), can_manage_settings=True,
            route_placement_version=1, production_split_version=1)
    finally:
        db_module.settings = prior_settings



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--node', default='node')
    for key in ['interruption-id', 'work-order', 'product', 'machine-id', 'reason', 'start-date', 'end-date']:
        parser.add_argument('--'+key, required=True)
    parser.add_argument('--produced-quantity', type=int, required=True)
    parser.add_argument('--remaining-quantity', type=int, required=True)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--expected-revision', default='')
    parser.add_argument('--expected-digest', default='')
    parser.add_argument('--actor', default='')
    args = parser.parse_args()
    target = {"interruptionId": args.interruption_id, "workOrder": args.work_order, "product": args.product,
        "machineId": args.machine_id, "producedQuantity": args.produced_quantity, "remainingQuantity": args.remaining_quantity, "reason": args.reason}
    original, proposed, review = prepare(args.database, args.node, target, {"startDate": args.start_date, "endDate": args.end_date})
    if args.apply:
        result = apply_proposal(args.database, original, proposed, review, expected_revision=args.expected_revision,
            expected_digest=args.expected_digest, actor=args.actor, reason=args.reason)
        review["appliedRevision"] = result["updatedAt"]
    print(json.dumps(review, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
