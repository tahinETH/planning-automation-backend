import copy
import importlib.util
import json
from pathlib import Path
import sqlite3

from app.database import preserve_live_operations


def test_live_operation_merge_marks_changed_calculation_stale_without_touching_inputs():
    incoming = {"machines": [{"id": "C-01", "currentJob": {"quantity": 480}}], "productionHistory": [], "planNeedsRecalculation": False}
    live = {"machines": [{"id": "C-01", "currentJob": {"quantity": 240}}], "productionHistory": [{"id": "delivery", "completedQuantity": 240}]}
    before = copy.deepcopy((incoming, live))
    saved = preserve_live_operations(incoming, live)
    assert saved["planNeedsRecalculation"] is True
    assert saved["machines"] == live["machines"]
    assert saved["productionHistory"] == live["productionHistory"]
    assert (incoming, live) == before


def test_unchanged_operations_do_not_invalidate_plan_but_old_clients_preserve_dirty_marker():
    live = {"machines": [], "productionHistory": [], "planNeedsRecalculation": True}
    incoming = {"machines": [], "productionHistory": []}
    assert preserve_live_operations(incoming, live)["planNeedsRecalculation"] is True
    incoming["planNeedsRecalculation"] = False
    assert preserve_live_operations(incoming, live)["planNeedsRecalculation"] is False
    live["planningEvents"] = [{"message": "note"}]
    assert preserve_live_operations(incoming, live)["planNeedsRecalculation"] is False


def test_readonly_export_is_consistent_and_does_not_modify_database(tmp_path):
    source = Path(__file__).resolve().parents[1] / "scripts/export_readonly_planning_snapshot.py"
    spec = importlib.util.spec_from_file_location("readonly_snapshot", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    database = tmp_path / "source.sqlite"
    with sqlite3.connect(database) as db:
        db.execute("CREATE TABLE planning_state(state_key TEXT, seed_json TEXT, updated_at TEXT)")
        db.execute("INSERT INTO planning_state VALUES(?,?,?)", ("default", json.dumps({"orders": [{"quantity": 480}]}), "2026-09-10T12:00:00Z"))
    before = database.read_bytes()
    snapshot = module.export_snapshot(database)
    assert snapshot["seed"]["orders"][0]["quantity"] == 480
    assert snapshot["sourceUpdatedAt"] == "2026-09-10T12:00:00Z"
    assert len(snapshot["seedSha256"]) == 64
    assert database.read_bytes() == before
    assert set(snapshot) == {"capturedAt", "sourceUpdatedAt", "seedSha256", "seed"}


def test_plan_and_order_dates_commit_together_and_conflict_or_failure_rolls_back(tmp_path, monkeypatch):
    from app import database as db_module
    from types import SimpleNamespace
    import pytest

    monkeypatch.setattr(db_module, "settings", SimpleNamespace(database_path=tmp_path / "atomic.sqlite", upload_dir=tmp_path / "uploads"))
    db_module.init_database()
    first = db_module.save_planning_state({"orders": [{"id": "order", "dueDate": "2026-09-05"}]}, expected_updated_at="")
    second = db_module.save_planning_state({"orders": [{"id": "order", "dueDate": "2026-09-12"}]}, expected_updated_at=first["updatedAt"])
    assert db_module.order_details()[0]["dueDate"] == "2026-09-12"
    with pytest.raises(db_module.PlanningStateConflict):
        db_module.save_planning_state({"orders": [{"id": "order", "dueDate": "2026-10-03"}]}, expected_updated_at=first["updatedAt"])
    assert db_module.order_details()[0]["dueDate"] == "2026-09-12"
    assert db_module.planning_state()["seed"] == second["seed"]
    original = db_module._save_orders
    def fail_after_dates(db, orders, timestamp, replace=False):
        original(db, orders, timestamp, replace)
        raise ValueError("injected failure after writing dates")
    monkeypatch.setattr(db_module, "_save_orders", fail_after_dates)
    with pytest.raises(ValueError, match="injected failure"):
        db_module.save_planning_state({"orders": [{"id": "order", "dueDate": "2026-10-03"}]}, expected_updated_at=second["updatedAt"])
    assert db_module.order_details()[0]["dueDate"] == "2026-09-12"
    assert db_module.planning_state()["updatedAt"] == second["updatedAt"]
    assert db_module.planning_state()["seed"] == second["seed"]


def test_interrupted_production_survives_planning_and_source_refresh():
    from app.production_merge import merge_production_refresh
    interruption = {"id": "pause-1", "chargeId": "charge-1", "process": "turning", "resourceId": "C-01", "producedQuantity": 200, "remainingQuantity": 400, "reason": "Çelik bitti"}
    live = {"productionInterruptions": [interruption], "wipLots": [{"id": "lot", "availableQuantity": 200}], "manualBatches": [{"id": "charge-1", "quantity": 400}]}
    incoming = {"productionInterruptions": [], "wipLots": [], "planNeedsRecalculation": False}
    before = copy.deepcopy(live)
    saved = preserve_live_operations(incoming, live)
    assert saved["productionInterruptions"] == [interruption]
    assert saved["planNeedsRecalculation"] is True
    refreshed = merge_production_refresh(incoming, live, {"productionInterruptions": [], "wipLots": []})
    assert refreshed["productionInterruptions"] == [interruption]
    assert refreshed["manualBatches"][0]["quantity"] == 400
    assert live == before


def test_interruption_save_reload_conflict_and_old_client_failure_are_atomic(tmp_path, monkeypatch):
    from app import database as db_module
    from types import SimpleNamespace
    import pytest
    monkeypatch.setattr(db_module, "settings", SimpleNamespace(database_path=tmp_path / "paused.sqlite", upload_dir=tmp_path / "uploads"))
    db_module.init_database()
    seed = {"productionInterruptions": [{"id": "pause-1", "producedQuantity": 200, "remainingQuantity": 400}], "orders": []}
    saved = db_module.save_planning_state(seed, expected_updated_at="", mode="operational")
    assert db_module.planning_state()["seed"] == seed
    with pytest.raises(ValueError, match="Yarım üretim"):
        db_module.save_planning_state({"orders": []}, expected_updated_at=saved["updatedAt"], mode="operational")
    assert db_module.planning_state()["seed"] == seed
    with pytest.raises(db_module.PlanningStateConflict):
        db_module.save_planning_state({"productionInterruptions": [], "orders": []}, expected_updated_at="old", mode="operational")
    assert db_module.planning_state()["updatedAt"] == saved["updatedAt"]


def test_partial_completion_version_gate_and_merge_preserve_release(tmp_path, monkeypatch):
    from app import database as db_module
    from types import SimpleNamespace
    import pytest
    monkeypatch.setattr(db_module, "settings", SimpleNamespace(database_path=tmp_path / "partial.sqlite", upload_dir=tmp_path / "uploads"))
    db_module.init_database()
    seed = {"productionInterruptions": [{"id": "split-1", "kind": "partial-completion", "producedQuantity": 450, "remainingQuantity": 1470}], "orders": []}
    with pytest.raises(ValueError, match="Kısmi üretim"):
        db_module.save_planning_state(seed, expected_updated_at="", mode="operational")
    saved = db_module.save_planning_state(seed, expected_updated_at="", mode="operational", production_split_version=1)
    for mode in ["operational", "planning"]:
        with pytest.raises(ValueError, match="Kısmi üretim"):
            db_module.save_planning_state({"orders": [], "productionInterruptions": []}, expected_updated_at=saved["updatedAt"], mode=mode, force=True)
        assert db_module.planning_state()["seed"] == saved["seed"]
        assert db_module.planning_state()["updatedAt"] == saved["updatedAt"]
    merged = db_module.save_planning_state({"orders": [], "productionInterruptions": []}, expected_updated_at=saved["updatedAt"], mode="planning", production_split_version=1)
    assert merged["seed"]["productionInterruptions"] == seed["productionInterruptions"]
    with pytest.raises(db_module.PlanningStateConflict):
        db_module.save_planning_state(seed, expected_updated_at=saved["updatedAt"], mode="operational", production_split_version=1)
    assert db_module.planning_state()["seed"] == merged["seed"]
    assert db_module.planning_state()["updatedAt"] == merged["updatedAt"]


def test_reviewed_partial_repair_preview_digest_apply_and_race_are_atomic(tmp_path, monkeypatch):
    from app import database as db_module
    from types import SimpleNamespace
    import subprocess
    import shutil
    import pytest
    root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location('partial_review', root / 'backend/scripts/review_turning_partial.py')
    review = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(review)
    db_path = tmp_path / 'repair.sqlite'
    monkeypatch.setattr(db_module, 'settings', SimpleNamespace(database_path=db_path, upload_dir=tmp_path / 'uploads'))
    db_module.init_database()
    # Synthetic source with reviewed quantities; no private exports enter the suite.
    code = r'''
const fs=require('node:fs');
const {migratePlanningSeed}=require('./lib/planning-state.ts');
const {recalculateManualScenario}=require('./lib/planning.ts');
const {replaceTurningCurrentJob}=require('./lib/production-interruption-actions.ts');
const seed=migratePlanningSeed(JSON.parse(fs.readFileSync('./data/planning-seed.json')));
const now=Date.now()/86400000+25569;
Object.assign(seed,{orders:[],customerDemand:undefined,openingStock:{},productionHistory:[],wipLots:[],wipMovements:[],processCurrentJobs:[],processOperationOverrides:[],productionInterruptions:[],manualBatches:[],calendarEvents:[],restrictions:[]});
const p=seed.products.find(p=>p.product==='R902719739');seed.products=[p];
const m=seed.machines.find(m=>m.id==='C-03');seed.machines=[m];m.active=true;m.shiftFactor=3;m.capacityFactor=1;m.rates[p.product]=200;p.eligibleMachines=[m.id];p.generalMachine=m.id;
m.currentJob={batchId:'original',product:p.product,workOrder:'638',quantity:1920,originalQuantity:1920,remainingQuantity:1920,start:now-3,end:now+1,dailyRate:600,diameter:p.diameter};m.availableStart=now+1;m.operationalAvailableStart=now+1;m.planEnd=now+90;
const b={id:'next',sequence:1,product:p.product,workOrder:'replacement',quantity:960,orderQuantity:2880,machineId:m.id,diameter:p.diameter,batchSize:960,dailyRate:600,availableStart:now+1,planEnd:now+90,reason:'',explanation:'',planColumn:13,existingQuantity:0,start:now+1,end:now+3,status:'planned'};
const next=replaceTurningCurrentJob(seed,recalculateManualScenario(seed,[b]),m.id,'next',{produced:true,quantity:450,reason:'priority'},now);
process.stdout.write(JSON.stringify(next.seed));
'''
    node = shutil.which('node')
    assert node
    seed = json.loads(subprocess.check_output([node, '--import', 'tsx', '-e', code], cwd=root / 'frontend', text=True))
    saved = db_module.save_planning_state(seed, expected_updated_at='', mode='operational', can_manage_settings=True)
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    today = datetime.now(ZoneInfo('Europe/Istanbul')).date()
    target = {'interruptionId': seed['productionInterruptions'][0]['id'], 'workOrder': '638', 'product': 'R902719739', 'machineId': 'C-03', 'producedQuantity': 450, 'remainingQuantity': 1470, 'reason': 'reviewed handoff'}
    scope = {'startDate': today.isoformat(), 'endDate': (today+timedelta(days=80)).isoformat()}
    original, proposed, checked = review.prepare(db_path, node, target, scope)
    assert review.prepare(db_path, node, target, scope)[2] == checked
    assert db_module.planning_state()['updatedAt'] == saved['updatedAt']
    assert checked['summary']['beforeUndated'] == 1920
    assert checked['summary']['afterUndated'] == 0
    assert proposed['productionHistory'] == original['productionHistory']
    assert proposed['wipLots'] == original['wipLots']
    assert proposed['machines'] == original['machines']
    kwargs = dict(expected_revision=checked['revision'], expected_digest=checked['digest'], actor='Reviewed operator', reason=target['reason'])
    with pytest.raises(ValueError, match='doğrulama'):
        review.apply_proposal(db_path, original, proposed, checked, **{**kwargs, 'expected_digest': 'bad'})
    before = db_module.planning_state()
    original_save_orders = db_module._save_orders
    def fail(*args, **kwargs):
        original_save_orders(*args, **kwargs)
        raise ValueError('injected transaction failure')
    monkeypatch.setattr(db_module, '_save_orders', fail)
    with pytest.raises(ValueError, match='injected'):
        review.apply_proposal(db_path, original, proposed, checked, **kwargs)
    assert db_module.planning_state() == before
    monkeypatch.setattr(db_module, '_save_orders', original_save_orders)
    applied = review.apply_proposal(db_path, original, proposed, checked, **kwargs)
    assert applied['seed']['productionInterruptions'][0]['kind'] == 'partial-completion'
    assert 'Reviewed operator' in applied['seed']['planningEvents'][0]['message']
    with pytest.raises(ValueError, match='değişti'):
        review.apply_proposal(db_path, original, proposed, checked, **kwargs)
    assert db_module.planning_state()['updatedAt'] == applied['updatedAt']
