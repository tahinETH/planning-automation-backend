"""Owned plans. Scenario writes never change orders or production records."""
from __future__ import annotations

import json
import uuid
from typing import Any
from fastapi import HTTPException
from .auth import CurrentUser
from .database import connection, now_iso

FACTS = ("productionInterruptions", "productionCancellations", "productionHistory", "wipLots", "wipMovements", "chargeJourneyNotes", "planningEvents", "processCurrentJobs")


def init_collaboration(db):
    db.executescript("""
      CREATE TABLE IF NOT EXISTS scenario_owners (
        scenario_id TEXT PRIMARY KEY REFERENCES scenarios(id) ON DELETE CASCADE,
        owner_id TEXT NOT NULL, owner_name TEXT NOT NULL, revision INTEGER NOT NULL,
        updated_at TEXT NOT NULL, source_id TEXT, source_revision INTEGER,
        shared INTEGER NOT NULL DEFAULT 0
      );
      CREATE TABLE IF NOT EXISTS scenario_requests (
        actor_id TEXT NOT NULL, request_id TEXT NOT NULL, request_hash TEXT NOT NULL,
        scenario_id TEXT NOT NULL, revision INTEGER NOT NULL, PRIMARY KEY(actor_id,request_id)
      );
      CREATE TABLE IF NOT EXISTS scenario_versions (
        scenario_id TEXT NOT NULL, revision INTEGER NOT NULL, actor_id TEXT NOT NULL,
        created_at TEXT NOT NULL, value_json TEXT NOT NULL,
        PRIMARY KEY(scenario_id, revision)
      );
      CREATE TABLE IF NOT EXISTS publication_previews (
        id TEXT PRIMARY KEY, actor_id TEXT NOT NULL, scenario_id TEXT NOT NULL, revision INTEGER NOT NULL,
        world_revision TEXT NOT NULL, previous_id TEXT, created_at TEXT NOT NULL, value_json TEXT NOT NULL
      );
      CREATE TABLE IF NOT EXISTS published_plans (
        id TEXT PRIMARY KEY, scope TEXT NOT NULL, scenario_id TEXT NOT NULL,
        scenario_revision INTEGER NOT NULL, actor_id TEXT NOT NULL, created_at TEXT NOT NULL,
        previous_id TEXT, world_revision TEXT NOT NULL, value_json TEXT NOT NULL
      );
      CREATE TABLE IF NOT EXISTS active_plans (scope TEXT PRIMARY KEY, publication_id TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS production_opening (
        id TEXT PRIMARY KEY, created_at TEXT NOT NULL, world_revision TEXT NOT NULL, state_hash TEXT NOT NULL, seed_json TEXT NOT NULL
      );
      CREATE TABLE IF NOT EXISTS production_commands (
        sequence INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT NOT NULL UNIQUE,
        actor_id TEXT NOT NULL, request_id TEXT NOT NULL, request_hash TEXT NOT NULL,
        kind TEXT NOT NULL, recorded_at TEXT NOT NULL, base_revision TEXT NOT NULL,
        result_revision TEXT NOT NULL, command_json TEXT NOT NULL, changes_json TEXT NOT NULL,
        UNIQUE(actor_id, request_id)
      );
    """)
    if "world_revision" not in {row[1] for row in db.execute("PRAGMA table_info(scenario_owners)")}:
        db.execute("ALTER TABLE scenario_owners ADD COLUMN world_revision TEXT NOT NULL DEFAULT ''")

    publication_columns = {row[1] for row in db.execute("PRAGMA table_info(published_plans)")}
    for column in ("actor_name", "scenario_name"):
        if column not in publication_columns:
            db.execute(f"ALTER TABLE published_plans ADD COLUMN {column} TEXT NOT NULL DEFAULT ''")


def _active_publication(db, scope):
    row = db.execute("""SELECT p.id,p.scope,p.scenario_id,p.scenario_revision,p.actor_id,
        p.actor_name,p.scenario_name,p.created_at FROM active_plans a
        JOIN published_plans p ON p.id=a.publication_id WHERE a.scope=?""", (scope,)).fetchone()
    if not row:
        return None
    return {"id": row["id"], "scope": row["scope"], "scenarioId": row["scenario_id"],
            "scenarioRevision": row["scenario_revision"], "scenarioName": row["scenario_name"] or None,
            "approvedBy": {"id": row["actor_id"], "name": row["actor_name"] or None},
            "approvedAt": row["created_at"]}


def planning_only(seed: dict) -> dict:
    value = json.loads(json.dumps(seed))
    for field in FACTS:
        value[field] = []
    for machine in value.get("machines", []):
        baseline = machine.get("operationalAvailableStart", machine.get("availableStart", 0))
        machine["currentJob"] = dict(workOrder="", product="", quantity=0, originalQuantity=0,
            remainingQuantity=0, start=baseline, end=baseline, dailyRate=0, diameter="")
    return value


def _record(db, scenario_id: str, user: CurrentUser, write=False):
    row = db.execute("""SELECT s.*,o.owner_id,o.owner_name,o.revision,o.updated_at,
        o.source_id,o.source_revision,o.shared,o.world_revision FROM scenarios s LEFT JOIN scenario_owners o
        ON o.scenario_id=s.id WHERE s.id=?""", (scenario_id,)).fetchone()
    if not row or (row["owner_id"] and row["owner_id"] != user.id and not row["shared"]):
        raise HTTPException(404, "Plan bulunamadı.")
    if write and row["owner_id"] != user.id:
        raise HTTPException(403, "Bu planı değiştiremezsiniz. Bana kopyala ile kişisel kopya oluşturun.")
    return {"id": row["id"], "name": row["name"], "createdAt": row["created_at"], "notes": row["notes"],
        "seed": json.loads(row["inputs_json"]), "result": json.loads(row["result_json"]),
        "ownerId": row["owner_id"], "ownerName": row["owner_name"], "revision": row["revision"] or 0,
        "updatedAt": row["updated_at"] or row["created_at"], "shared": bool(row["shared"]),
        "worldRevision": row["world_revision"] or "", "sourceId": row["source_id"], "sourceRevision": row["source_revision"],
        "canEdit": row["owner_id"] == user.id, "legacy": row["owner_id"] is None}


def get_scenario(scenario_id, user):
    with connection() as db:
        return _record(db, scenario_id, user)


def list_scenarios(user, limit=None, offset=0):
    with connection() as db:
        where = "o.owner_id=? OR o.shared=1 OR o.owner_id IS NULL"
        args = (user.id,)
        total = db.execute(f"SELECT COUNT(*) FROM scenarios s LEFT JOIN scenario_owners o ON o.scenario_id=s.id WHERE {where}", args).fetchone()[0]
        query = f"SELECT s.id FROM scenarios s LEFT JOIN scenario_owners o ON o.scenario_id=s.id WHERE {where} ORDER BY s.created_at DESC,s.id DESC"
        if limit is not None:
            query += " LIMIT ? OFFSET ?"
            args += (limit, offset)
        records = [_record(db, row["id"], user) for row in db.execute(query, args).fetchall()]
    if limit is None:
        return records
    items = [{**{k: v for k, v in r.items() if k not in ("seed", "result")},
        "plannedBatchCount": max(0, int(r["result"].get("summary", {}).get("plannedBatchCount", 0))),
        "planRun": r["result"].get("planRun") or r["seed"].get("activePlanRun")} for r in records]
    return dict(items=items, total=total, limit=limit, offset=offset, hasMore=offset + len(items) < total)


def _save(db, value, user, previous=None, source=None):
    timestamp = now_iso()
    revision = previous["revision"] + 1 if previous else 1
    seed = planning_only(value["seed"])
    created = previous["createdAt"] if previous else timestamp
    db.execute("""INSERT INTO scenarios(id,name,created_at,notes,inputs_json,result_json) VALUES(?,?,?,?,?,?)
      ON CONFLICT(id) DO UPDATE SET name=excluded.name,notes=excluded.notes,
      inputs_json=excluded.inputs_json,result_json=excluded.result_json""",
      (value["id"], value["name"].strip(), created, value.get("notes", ""), json.dumps(seed), json.dumps(value["result"])))
    db.execute("""INSERT INTO scenario_owners(scenario_id,owner_id,owner_name,revision,updated_at,source_id,source_revision)
      VALUES(?,?,?,?,?,?,?) ON CONFLICT(scenario_id) DO UPDATE SET revision=excluded.revision,updated_at=excluded.updated_at""",
      (value["id"], user.id, user.name, revision, timestamp, source["id"] if source else None, source["revision"] if source else None))
    db.execute("UPDATE scenario_owners SET world_revision=? WHERE scenario_id=?", (value.get("worldRevision", previous.get("worldRevision", "") if previous else ""), value["id"]))
    saved = _record(db, value["id"], user)
    db.execute("INSERT INTO scenario_versions VALUES(?,?,?,?,?)", (value["id"], revision, user.id, timestamp, json.dumps(saved)))
    return saved


def save_scenario(value, user):
    with connection() as db:
        db.execute("BEGIN IMMEDIATE")
        exists = db.execute("SELECT id FROM scenarios WHERE id=?", (value["id"],)).fetchone()
        previous = _record(db, value["id"], user, write=True) if exists else None
        if previous and value.get("revision") != previous["revision"]:
            raise HTTPException(409, "Plan başka bir oturumda değişti. Yerel kopyayı koruyun ve planı yeniden açın.")
        if not previous and db.execute("SELECT 1 FROM scenario_versions WHERE scenario_id=?", (value["id"],)).fetchone():
            raise HTTPException(409, "Silinmiş plan kimliği tekrar kullanılamaz. Yeni kopya oluşturun.")
        if not previous and value.get("revision") not in (None, 0):
            raise HTTPException(409, "Yeni plan sürümü geçersiz.")
        return _save(db, value, user, previous)


def fork_scenario(scenario_id, user):
    with connection() as db:
        db.execute("BEGIN IMMEDIATE")
        source = _record(db, scenario_id, user)
        return _save(db, {**source, "id": str(uuid.uuid4()), "name": source["name"] + " — kopya"}, user, source=source)


def share_scenario(scenario_id, revision, shared, user):
    with connection() as db:
        db.execute("BEGIN IMMEDIATE")
        source = _record(db, scenario_id, user, write=True)
        if source["revision"] != revision:
            raise HTTPException(409, "Plan değişti. Listeyi yenileyin.")
        db.execute("UPDATE scenario_owners SET shared=? WHERE scenario_id=?", (int(shared), scenario_id))
        return _save(db, source, user, source)


def delete_scenario(scenario_id, revision, user):
    with connection() as db:
        db.execute("BEGIN IMMEDIATE")
        source = _record(db, scenario_id, user, write=True)
        if source["revision"] != revision:
            raise HTTPException(409, "Plan değişti. Listeyi yenileyin.")
        db.execute("DELETE FROM scenarios WHERE id=?", (scenario_id,))
    return {"ok": True}


def run_domain(request):
    """Run the shipped TypeScript rules. Input, execution time and output are bounded."""
    import hashlib
    import os
    import subprocess
    import tempfile
    from pathlib import Path
    runtime = Path(__file__).resolve().parents[1] / "runtime" / "collaboration-runtime.cjs"
    manifest = json.loads(runtime.with_suffix(".cjs.json").read_text())
    if hashlib.sha256(runtime.read_bytes()).hexdigest() != manifest["runtimeSha256"]:
        raise HTTPException(503, "Üretim kuralları doğrulanamadı.")
    data = json.dumps(request, allow_nan=False).encode()
    if len(data) > 32 * 1024 * 1024:
        raise HTTPException(413, "İşlem boyutu sınırı aşıldı.")
    env = {k: v for k, v in os.environ.items() if k in {"PATH", "SYSTEMROOT"}}
    env["TZ"] = "Europe/Istanbul"
    try:
        with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as errors:
            subprocess.run([os.environ.get("DELIVERY_NODE_BINARY", "node"), "--max-old-space-size=512", str(runtime)],
                input=data, stdout=output, stderr=errors, timeout=20, check=True, env=env)
            if output.tell() > 32 * 1024 * 1024:
                raise ValueError("output limit")
            output.seek(0)
            result = json.load(output)
    except (OSError, subprocess.SubprocessError, ValueError) as error:
        raise HTTPException(503, "İşlem doğrulanamadı. Yerel isteği koruyun.") from error
    if result.get("error"):
        raise HTTPException(409 if result.get("conflict") else 422, result["error"])
    if not isinstance(result.get("seed"), dict) or not isinstance(result.get("result"), dict):
        raise HTTPException(503, "İşlem yanıtı geçersiz.")
    result["engineHash"] = manifest["runtimeSha256"]
    return result


def patch_scenario(scenario_id, value, user):
    from .planning_delta import apply_delta, state_hash
    with connection() as db:
        db.execute("BEGIN IMMEDIATE")
        current = _record(db, scenario_id, user, write=True)
        request_hash = state_hash(value)
        receipt = db.execute("SELECT * FROM scenario_requests WHERE actor_id=? AND request_id=?", (user.id, value["requestId"])).fetchone()
        if receipt:
            if receipt["request_hash"] != request_hash or receipt["scenario_id"] != scenario_id:
                raise HTTPException(409, "İstek kimliği başka bir işlem için kullanıldı.")
            return {"requestId": value["requestId"], "scenario": current, "appliedRevision": receipt["revision"], "replayed": True}
        if value["revision"] != current["revision"]:
            raise HTTPException(409, "Taslak başka bir oturumda değişti. Yerel kopyayı koruyun.")
        world = _world(db)
        if value.get("worldRevision") != world["updatedAt"]:
            raise HTTPException(409, "Ortak üretim değişti. Taslağı güncel üretimle yeniden inceleyin.")
        seed = apply_delta(current["seed"], value["delta"])
        normalized = run_domain({"action": "draft", "seed": seed, "world": world["seed"]})
        saved = _save(db, {**current, **normalized, "worldRevision": world["updatedAt"]}, user, current)
        db.execute("INSERT INTO scenario_requests VALUES(?,?,?,?,?)", (user.id, value["requestId"], request_hash, scenario_id, saved["revision"]))
        return {"requestId": value["requestId"], "scenario": saved, "appliedRevision": saved["revision"], "replayed": False}


def _world(db):
    from .planning_delta import state_hash
    row = db.execute("SELECT * FROM planning_state WHERE state_key='default'").fetchone()
    if not row:
        raise HTTPException(409, "Ortak üretim kaydı bulunamadı.")
    seed = json.loads(row["seed_json"])
    return {"seed": seed, "updatedAt": row["updated_at"], "updatedBy": {"id": row["updated_by_id"], "name": row["updated_by_name"]}, "stateHash": state_hash(seed), "patchVersion": 1}


def production_command(value, user):
    from .database import save_planning_state
    from .planning_delta import state_hash, build_delta
    if value["command"].get("kind") in {"reviseOfficialOrder", "deactivateParameters"} and not user.is_admin:
        raise HTTPException(403, "Resmi sipariş revizyonunu yalnız yönetici onaylayabilir.")
    with connection() as db:
        db.execute("BEGIN IMMEDIATE")
        current = _world(db)
        digest = state_hash(value)
        receipt = db.execute("SELECT * FROM production_commands WHERE actor_id=? AND request_id=?", (user.id, value["requestId"])).fetchone()
        if receipt:
            if receipt["request_hash"] != digest:
                raise HTTPException(409, "İstek kimliği başka bir işlem için kullanıldı.")
            return {"current": current, "requestId": value["requestId"], "appliedRevision": receipt["result_revision"], "replayed": True}
        if value["command"]["kind"] == "deactivateParameters":
            from .planning_delta import apply_delta
            delta = value["command"]["args"][0]["delta"]
            fields = set(delta.get("set", {})) | set(delta.get("arrays", {})) | set(delta.get("remove", []))
            if fields - {"products", "preferences", "restrictions", "machines", "processMasterData", "productWeights", "rawMaterialSettings"}:
                raise HTTPException(422, "Pasif atama girdileri geçersiz.")
            assert_shared_inputs_only(current["seed"], apply_delta(current["seed"], delta), True)
        db.execute("INSERT OR IGNORE INTO production_opening VALUES(?,?,?,?,?)", ("default", now_iso(), current["updatedAt"], current["stateHash"], json.dumps(current["seed"])))
        accepted = run_domain({"action": "command", "seed": current["seed"], "command": value["command"], "expectedBasis": value["expectedBasis"]})
        saved = save_planning_state(accepted["seed"], current["updatedAt"], mode="operational", actor_id=user.id,
            actor_name=user.name, can_manage_settings=user.is_admin, flow_settings_version=1, route_placement_version=1,
            production_split_version=1, process_wait_settings_version=1, internal_connection=db)
        if value["command"]["kind"] == "reviseOfficialOrder":
            request = accepted["orderReview"]["requested"]
            original = next(row for row in current["seed"]["orders"] if row["id"] == request["orderId"])
            timestamp = now_iso()
            db.execute("INSERT INTO order_revisions VALUES(?,?,?,?,?,?,?,?,?,?,?)", (str(uuid.uuid4()), request["orderId"], original["product"], "approved", timestamp, timestamp,
                json.dumps(original), json.dumps(request), json.dumps(accepted["orderReview"]["impact"]), json.dumps(saved["seed"]), json.dumps(accepted["result"])))
        db.execute("""INSERT INTO production_commands(id,actor_id,request_id,request_hash,kind,recorded_at,base_revision,
            result_revision,command_json,changes_json) VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (str(uuid.uuid4()), user.id, value["requestId"], digest, value["command"]["kind"], now_iso(), current["updatedAt"],
             saved["updatedAt"], json.dumps(value["command"]), json.dumps(build_delta(current["seed"], saved["seed"]))))
        return {"current": saved, "requestId": value["requestId"], "appliedRevision": saved["updatedAt"], "replayed": False}


def publication_preview(scenario_id, value, user):
    if not user.is_admin:
        raise HTTPException(403, "Planı yalnız yönetici yayınlayabilir.")
    with connection() as db:
        db.execute("BEGIN IMMEDIATE")
        scenario = _record(db, scenario_id, user)
        current = _world(db)
        scope = current["seed"].get("productionArea", "torna")
        active = db.execute("SELECT publication_id FROM active_plans WHERE scope=?", (scope,)).fetchone()
        previous_id = active[0] if active else None
        if (scenario["revision"] != value["revision"] or current["updatedAt"] != value["worldRevision"] or previous_id != value.get("previousId")):
            raise HTTPException(409, "Plan veya üretim kaydı değişti. Önizlemeyi yenileyin.")
        if scenario.get("worldRevision") != current["updatedAt"]:
            raise HTTPException(409, "Taslak güncel üretimle kaydedilmedi. Önce taslağı inceleyip kaydedin.")
        accepted = run_domain({"action": "publish", "seed": current["seed"], "draft": scenario["seed"]})
        preview_id = str(uuid.uuid4())
        db.execute("INSERT INTO publication_previews VALUES(?,?,?,?,?,?,?,?)", (preview_id, user.id, scenario_id, scenario["revision"], current["updatedAt"], previous_id, now_iso(), json.dumps(accepted)))
        before = {row["id"]: row for row in current["seed"].get("manualBatches", [])}
        after = {row["id"]: row for row in accepted["seed"].get("manualBatches", [])}
        changes = [{"id": key, "before": before.get(key), "after": after.get(key)} for key in dict.fromkeys([*before, *after]) if before.get(key) != after.get(key)]
        return {"previewId": preview_id, "scenarioId": scenario_id, "revision": scenario["revision"], "name": scenario["name"],
                "worldRevision": current["updatedAt"], "previousId": previous_id, "changes": changes,
                "batchCount": len(after), "quantity": sum(row.get("quantity", 0) for row in after.values())}


def publish_scenario(scenario_id, value, user):
    from .database import save_planning_state
    if not user.is_admin:
        raise HTTPException(403, "Planı yalnız yönetici yayınlayabilir.")
    with connection() as db:
        db.execute("BEGIN IMMEDIATE")
        current = _world(db)
        committed = db.execute("SELECT id FROM published_plans WHERE id=? AND scenario_id=? AND actor_id=?", (value.get("previewId"), scenario_id, user.id)).fetchone()
        if committed:
            return {"publicationId": committed["id"], "current": current, "replayed": True,
                    "activePublication": _active_publication(db, current["seed"].get("productionArea", "torna"))}
        scenario = _record(db, scenario_id, user)
        preview = db.execute("SELECT * FROM publication_previews WHERE id=? AND actor_id=? AND scenario_id=?", (value.get("previewId"), user.id, scenario_id)).fetchone()
        if not preview:
            raise HTTPException(409, "Yayınlamadan önce plan önizlemesini inceleyin.")
        scope = current["seed"].get("productionArea", "torna")
        active = db.execute("SELECT publication_id FROM active_plans WHERE scope=?", (scope,)).fetchone()
        previous_id = active[0] if active else None
        if (scenario["revision"] != preview["revision"] or current["updatedAt"] != preview["world_revision"] or previous_id != preview["previous_id"]):
            raise HTTPException(409, "Önizlemeden sonra plan veya üretim değişti. Önizlemeyi yenileyin.")
        accepted = json.loads(preview["value_json"])
        from pathlib import Path
        from datetime import datetime, timezone
        manifest = json.loads((Path(__file__).resolve().parents[1] / "runtime" / "collaboration-runtime.cjs.json").read_text())
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(preview["created_at"])).total_seconds()
        if age > 600 or accepted.get("engineHash") != manifest["runtimeSha256"]:
            raise HTTPException(409, "Plan önizlemesi güncel değil. Önizlemeyi yenileyin.")
        saved = save_planning_state(accepted["seed"], current["updatedAt"], mode="planning", actor_id=user.id,
            actor_name=user.name, can_manage_settings=True, flow_settings_version=1, route_placement_version=1,
            production_split_version=1, process_wait_settings_version=1, internal_connection=db)
        publication_id = preview["id"]
        db.execute("""INSERT INTO published_plans(id,scope,scenario_id,scenario_revision,actor_id,created_at,
            previous_id,world_revision,value_json,actor_name,scenario_name) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            (publication_id, scope, scenario_id, scenario["revision"], user.id, now_iso(), previous_id,
             current["updatedAt"], json.dumps({"seed": saved["seed"], "result": accepted["result"]}), user.name, scenario["name"]))
        db.execute("INSERT INTO active_plans VALUES(?,?) ON CONFLICT(scope) DO UPDATE SET publication_id=excluded.publication_id", (scope, publication_id))
        return {"publicationId": publication_id, "current": saved, "replayed": False, "activePublication": _active_publication(db, scope)}


def collaboration_status():
    with connection() as db:
        db.execute("BEGIN")
        current = _world(db)
        active = _active_publication(db, current["seed"].get("productionArea", "torna"))
        return {"worldRevision": current["updatedAt"], "publicationId": active["id"] if active else None, "activePublication": active,
                "lastCommand": db.execute("SELECT COALESCE(MAX(sequence),0) FROM production_commands").fetchone()[0]}


def assert_shared_inputs_only(current, candidate, is_admin):
    if not is_admin:
        raise HTTPException(403, "Ortak girdileri yalnız yönetici değiştirebilir. Planı kişisel taslakta düzenleyin.")
    if current is None:
        if any(candidate.get(field) for field in (*FACTS, "manualBatches", "savedBatches", "processOperationOverrides")) or any(row.get("currentJob", {}).get("quantity", 0) for row in candidate.get("machines", [])):
            raise HTTPException(409, "Fiziksel başlangıç kaydı ayrı doğrulama gerektirir.")
        return
    for field in (*FACTS, "manualBatches", "savedBatches", "processOperationOverrides"):
        if candidate.get(field, []) != current.get(field, []):
            raise HTTPException(409, "Ortak üretim için işlem komutunu, plan için kişisel taslak ve Planı yayınla kullanın.")
    before = {row["id"]: row for row in current.get("machines", [])}
    after = {row["id"]: row for row in candidate.get("machines", [])}
    for identity in before.keys() | after.keys():
        old, new = before.get(identity), after.get(identity)
        if old is not None and new is not None:
            changed = (old.get("currentJob"), old.get("operationalAvailableStart")) != (new.get("currentJob"), new.get("operationalAvailableStart"))
        else:
            job = (old or new).get("currentJob") or {}
            changed = bool(job.get("product") or job.get("workOrder") or job.get("quantity") or job.get("remainingQuantity") or job.get("batchId"))
        if changed:
            raise HTTPException(409, "Mevcut üretim yalnız üretim komutuyla değiştirilebilir.")


def request_status(request_id, kind, user):
    with connection() as db:
        db.execute("BEGIN")
        if kind == "draft":
            row = db.execute("SELECT * FROM scenario_requests WHERE actor_id=? AND request_id=?", (user.id, request_id)).fetchone()
            return {"committed": False} if not row else {"committed": True, "requestId": request_id, "appliedRevision": row["revision"], "scenario": _record(db, row["scenario_id"], user)}
        if kind == "publication":
            row = db.execute("SELECT * FROM published_plans WHERE actor_id=? AND id=?", (user.id, request_id)).fetchone()
            return {"committed": False} if not row else {"committed": True, "publicationId": request_id, "current": _world(db),
                "activePublication": _active_publication(db, row["scope"])}
        if kind != "production":
            raise HTTPException(422, "Kayıt türü geçersiz.")
        row = db.execute("SELECT * FROM production_commands WHERE actor_id=? AND request_id=?", (user.id, request_id)).fetchone()
        return {"committed": False} if not row else {"committed": True, "requestId": request_id, "appliedRevision": row["result_revision"], "current": _world(db)}
