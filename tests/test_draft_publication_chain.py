from app import collaboration


def _command(db, sequence, kind, base, result):
    db.execute("INSERT INTO production_commands(sequence,id,actor_id,request_id,request_hash,kind,recorded_at,base_revision,result_revision,command_json,changes_json) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
               (sequence, f"c{sequence}", "u", f"r{sequence}", "h", kind, "t", base, result, "{}", "{}"))


def test_only_notes_and_queue_locks_since_the_draft_keep_it_publishable():
    import sqlite3
    db = sqlite3.connect(":memory:"); db.row_factory = sqlite3.Row
    collaboration_tables = "CREATE TABLE production_commands(sequence INTEGER,id TEXT,actor_id TEXT,request_id TEXT,request_hash TEXT,kind TEXT,recorded_at TEXT,base_revision TEXT,result_revision TEXT,command_json TEXT,changes_json TEXT)"
    db.execute(collaboration_tables)
    _command(db, 1, "saveJourneyNote", "a", "b")
    _command(db, 2, "setMachineQueueLock", "b", "c")
    _command(db, 3, "completeCurrentJob", "c", "d")
    assert collaboration._only_plan_neutral_since(db, "a", "c") is True
    assert collaboration._only_plan_neutral_since(db, "a", "d") is False
    assert collaboration._only_plan_neutral_since(db, "a", "unknown") is False
