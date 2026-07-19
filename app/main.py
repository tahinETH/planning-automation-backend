from __future__ import annotations

import json
import mimetypes
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .auth import CurrentUser, create_session, current_user
from .config import settings
from .database import all_feedback, connection, feedback_record, init_database, now_iso, order_details, planning_state, revisions, save_orders, save_planning_state, scenarios
from .models import CommentCreate, CommentUpdate, FeedbackCreate, FeedbackUpdate, LoginRequest, PlanningStatePayload, RevisionPayload, ScenarioPayload
from .order_import import MAX_XLSX_BYTES, OrderImportError, parse_order_xlsx


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_database()
    yield


app = FastAPI(title="Selsa Planlama API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins), allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


def require_feedback(db, feedback_id: str) -> dict[str, Any]:
    record = feedback_record(db, feedback_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Geri bildirim bulunamadı")
    return record


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/auth/login")
def login(payload: LoginRequest):
    return {"token": create_session(payload.password), "name": "Planlama Yöneticisi"}


@app.get("/api/me")
def me(user: CurrentUser = Depends(current_user)):
    return {"id": user.id, "name": user.name}


@app.get("/api/orders")
def get_orders(_: CurrentUser = Depends(current_user)):
    return order_details()


@app.put("/api/orders")
def put_orders(payload: list[dict[str, Any]], _: CurrentUser = Depends(current_user)):
    save_orders(payload)
    return {"ok": True}


@app.post("/api/order-imports/preview")
async def preview_order_import(file: UploadFile = File(...), _: CurrentUser = Depends(current_user)):
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=422, detail="Yalnızca .xlsx dosyası yükleyebilirsiniz.")
    content = await file.read(MAX_XLSX_BYTES + 1)
    try:
        preview = parse_order_xlsx(content)
    except OrderImportError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {"fileName": Path(file.filename).name, **preview}


@app.get("/api/planning-state")
def get_planning_state(_: CurrentUser = Depends(current_user)):
    return planning_state()


@app.put("/api/planning-state")
def put_planning_state(payload: PlanningStatePayload, _: CurrentUser = Depends(current_user)):
    return save_planning_state(payload.seed)


@app.get("/api/scenarios")
def get_scenarios(_: CurrentUser = Depends(current_user)):
    return scenarios()


@app.post("/api/scenarios", status_code=201)
def post_scenario(payload: ScenarioPayload, _: CurrentUser = Depends(current_user)):
    value = payload.model_dump()
    with connection() as db:
        db.execute("""INSERT INTO scenarios(id,name,created_at,notes,inputs_json,result_json) VALUES(?,?,?,?,?,?)
        ON CONFLICT(id) DO UPDATE SET name=excluded.name,created_at=excluded.created_at,notes=excluded.notes,inputs_json=excluded.inputs_json,result_json=excluded.result_json""",
        (payload.id, payload.name, payload.createdAt, payload.notes, json.dumps(payload.seed), json.dumps(payload.result)))
    save_orders(payload.seed.get("orders", []))
    return value


@app.delete("/api/scenarios/{scenario_id}")
def remove_scenario(scenario_id: str, _: CurrentUser = Depends(current_user)):
    with connection() as db:
        db.execute("DELETE FROM scenarios WHERE id=?", (scenario_id,))
    return {"ok": True}


@app.get("/api/revisions")
def get_revisions(_: CurrentUser = Depends(current_user)):
    return revisions()


@app.post("/api/revisions", status_code=201)
def post_revision(payload: RevisionPayload, _: CurrentUser = Depends(current_user)):
    with connection() as db:
        db.execute("""INSERT INTO order_revisions(id,order_id,product,status,created_at,approved_at,original_json,request_json,impact_json,seed_json,result_json)
        VALUES(?,?,?,?,?,?,?,?,?,?,?)""", (payload.id, payload.orderId, payload.product, payload.status, payload.createdAt, payload.approvedAt,
        json.dumps(payload.original), json.dumps(payload.requested), json.dumps(payload.impact), json.dumps(payload.seed), json.dumps(payload.result)))
    save_orders(payload.seed.get("orders", []))
    return payload.model_dump()


@app.get("/api/feedbacks")
def get_feedbacks(_: CurrentUser = Depends(current_user)):
    return all_feedback()


@app.post("/api/feedbacks", status_code=201)
def create_feedback(payload: FeedbackCreate, user: CurrentUser = Depends(current_user)):
    feedback_id, timestamp = str(uuid.uuid4()), now_iso()
    with connection() as db:
        db.execute("INSERT INTO feedbacks(id,author_id,author_name,page_path,body,status,priority,created_at,updated_at) VALUES(?,?,?,?,?,'active',?,?,?)",
                   (feedback_id, user.id, user.name, payload.page_path, payload.body.strip(), payload.priority, timestamp, timestamp))
        return feedback_record(db, feedback_id)


@app.patch("/api/feedbacks/{feedback_id}")
def update_feedback(feedback_id: str, payload: FeedbackUpdate, _: CurrentUser = Depends(current_user)):
    with connection() as db:
        current = require_feedback(db, feedback_id)
        body = payload.body.strip() if payload.body is not None else current["body"]
        status = payload.status or current["status"]
        priority = payload.priority if payload.priority is not None else current["priority"]
        timestamp = now_iso()
        resolved_at = timestamp if status == "resolved" else None
        canceled_at = timestamp if status == "canceled" else None
        db.execute("UPDATE feedbacks SET body=?,status=?,priority=?,updated_at=?,resolved_at=?,canceled_at=? WHERE id=?", (body, status, priority, timestamp, resolved_at, canceled_at, feedback_id))
        return feedback_record(db, feedback_id)


@app.post("/api/feedbacks/{feedback_id}/comments", status_code=201)
def create_comment(feedback_id: str, payload: CommentCreate, user: CurrentUser = Depends(current_user)):
    comment_id, timestamp = str(uuid.uuid4()), now_iso()
    with connection() as db:
        require_feedback(db, feedback_id)
        db.execute("INSERT INTO feedback_comments(id,feedback_id,author_id,author_name,body,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
                   (comment_id, feedback_id, user.id, user.name, payload.body.strip(), timestamp, timestamp))
        db.execute("UPDATE feedbacks SET updated_at=? WHERE id=?", (timestamp, feedback_id))
        return feedback_record(db, feedback_id)


@app.patch("/api/comments/{comment_id}")
def update_comment(comment_id: str, payload: CommentUpdate, _: CurrentUser = Depends(current_user)):
    with connection() as db:
        row = db.execute("SELECT feedback_id FROM feedback_comments WHERE id=?", (comment_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Yorum bulunamadı")
        timestamp = now_iso()
        db.execute("UPDATE feedback_comments SET body=?,updated_at=? WHERE id=?", (payload.body.strip(), timestamp, comment_id))
        db.execute("UPDATE feedbacks SET updated_at=? WHERE id=?", (timestamp, row["feedback_id"]))
        return feedback_record(db, row["feedback_id"])


@app.post("/api/feedbacks/{feedback_id}/attachments", status_code=201)
async def upload_attachments(feedback_id: str, files: list[UploadFile] = File(...), user: CurrentUser = Depends(current_user)):
    with connection() as db:
        require_feedback(db, feedback_id)
    for upload in files:
        content_type = upload.content_type or mimetypes.guess_type(upload.filename or "")[0] or "application/octet-stream"
        kind = "image" if content_type.startswith("image/") else "voice" if content_type.startswith("audio/") else None
        if kind is None:
            raise HTTPException(status_code=415, detail="Yalnızca görüntü veya ses dosyası yüklenebilir")
        content = await upload.read()
        limit = 20 * 1024 * 1024 if kind == "image" else 50 * 1024 * 1024
        if not content or len(content) > limit:
            raise HTTPException(status_code=413, detail="Dosya boyutu sınırı aşıldı")
        suffix = Path(upload.filename or "").suffix[:10]
        attachment_id, storage_key = str(uuid.uuid4()), f"{uuid.uuid4().hex}{suffix}"
        (settings.upload_dir / storage_key).write_bytes(content)
        timestamp = now_iso()
        with connection() as db:
            db.execute("INSERT INTO feedback_attachments(id,feedback_id,author_id,kind,original_name,content_type,size,storage_key,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                       (attachment_id, feedback_id, user.id, kind, upload.filename or f"{kind}{suffix}", content_type, len(content), storage_key, timestamp))
            db.execute("UPDATE feedbacks SET updated_at=? WHERE id=?", (timestamp, feedback_id))
    with connection() as db:
        return feedback_record(db, feedback_id)


@app.get("/api/attachments/{attachment_id}/content")
def attachment_content(attachment_id: str, _: CurrentUser = Depends(current_user)):
    with connection() as db:
        row = db.execute("SELECT * FROM feedback_attachments WHERE id=?", (attachment_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Dosya bulunamadı")
    path = settings.upload_dir / row["storage_key"]
    if not path.exists():
        raise HTTPException(status_code=404, detail="Dosya bulunamadı")
    return FileResponse(path, media_type=row["content_type"], filename=row["original_name"])


@app.delete("/api/attachments/{attachment_id}")
def delete_attachment(attachment_id: str, _: CurrentUser = Depends(current_user)):
    with connection() as db:
        row = db.execute("SELECT feedback_id,storage_key FROM feedback_attachments WHERE id=?", (attachment_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Dosya bulunamadı")
        db.execute("DELETE FROM feedback_attachments WHERE id=?", (attachment_id,))
        db.execute("UPDATE feedbacks SET updated_at=? WHERE id=?", (now_iso(), row["feedback_id"]))
    (settings.upload_dir / row["storage_key"]).unlink(missing_ok=True)
    return {"ok": True}
