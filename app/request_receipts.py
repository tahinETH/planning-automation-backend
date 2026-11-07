"""Actor-scoped immutable receipts, committed in the caller's transaction."""
import json
from fastapi import HTTPException
from .planning_delta import state_hash


def replay(db, actor_id, kind, request_id, payload):
    if not request_id:
        return None
    row = db.execute("SELECT request_hash,result_json FROM operation_requests WHERE actor_id=? AND kind=? AND request_id=?",
                     (actor_id, kind, request_id)).fetchone()
    if row is None:
        return None
    if row["request_hash"] != state_hash(payload):
        raise HTTPException(409, "İstek kimliği farklı bir içerikle tekrar kullanılamaz.")
    return json.loads(row["result_json"])


def record(db, actor_id, kind, request_id, payload, result):
    if request_id:
        db.execute("INSERT INTO operation_requests VALUES(?,?,?,?,?)",
                   (actor_id, kind, request_id, state_hash(payload), json.dumps(result)))
