"""Authenticated type requests. A decision and its input change commit together."""
from copy import deepcopy
import json
import re
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from . import database as store
from .auth import CurrentUser, current_user, require_admin
from .product_type_deletion import product_type_deletion_blockers, remove_unused_product_type

router = APIRouter(prefix="/api/type-requests", tags=["type-requests"])


class CreateTypeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_.:-]+$")
    product: str = Field(min_length=1, max_length=128)
    reason: str = Field(min_length=1, max_length=1000)


class ReviewTypeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expectedRevision: int = Field(ge=1)
    expectedWorldRevision: str = Field(min_length=1, max_length=128)
    decision: Literal["delete", "retire", "reactivate", "reject"]
    note: str = Field(min_length=1, max_length=1000)


def _state(connection):
    row = connection.execute("SELECT seed_json,updated_at FROM planning_state WHERE state_key='default'").fetchone()
    if row is None:
        raise HTTPException(409, "Ortak plan henüz hazır değil.")
    return json.loads(row["seed_json"]), row["updated_at"]


def _product(seed, code):
    return next((row for row in [*seed.get("products", []), *(seed.get("processMasterData") or {}).get("products", [])] if row.get("product", "").strip().upper() == code), None)


def _view(row):
    return {"id": row["id"], "product": row["product"], "reason": row["reason"], "status": row["status"],
        "revision": row["revision"], "createdAt": row["created_at"], "requestedBy": {"id": row["actor_id"], "name": row["actor_name"]},
        "reviewedAt": row["reviewed_at"], "reviewerName": row["reviewer_name"], "decision": row["decision"],
        "note": row["review_note"], "resultRevision": row["result_revision"]}


def _owned(connection, identity, user):
    row = connection.execute("SELECT * FROM type_management_requests WHERE id=?", (identity,)).fetchone()
    if row is None or (not user.is_admin and row["actor_id"] != user.id):
        raise HTTPException(404, "Talep bulunamadı.")
    return row


@router.get("")
def list_type_requests(limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0), user: CurrentUser = Depends(current_user)):
    with store.connection() as connection:
        where, values = ("", ()) if user.is_admin else ("WHERE actor_id=?", (user.id,))
        rows = connection.execute(f"SELECT * FROM type_management_requests {where} ORDER BY created_at DESC,id LIMIT ? OFFSET ?", (*values, limit, offset)).fetchall()
        total = connection.execute(f"SELECT COUNT(*) FROM type_management_requests {where}", values).fetchone()[0]
        return {"items": [_view(row) for row in rows], "total": total, "offset": offset, "limit": limit}


@router.post("")
def create_type_request(payload: CreateTypeRequest, user: CurrentUser = Depends(current_user)):
    product, reason = payload.product.strip().upper(), payload.reason.strip()
    if not reason or not re.fullmatch(r"[A-Z0-9._/-]{1,128}", product):
        raise HTTPException(422, "Geçerli tip kodu ve talep açıklaması girin.")
    with store.connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        existing = connection.execute("SELECT * FROM type_management_requests WHERE id=?", (payload.id,)).fetchone()
        if existing:
            if (existing["actor_id"], existing["product"], existing["reason"]) != (user.id, product, reason):
                raise HTTPException(409, "Talep kimliği başka bir işlemde kullanıldı.")
            return {"request": _view(existing), "replayed": True}
        seed, _ = _state(connection)
        if _product(seed, product) is None:
            raise HTTPException(422, "Tip bulunamadı. Güncel parametreleri yükleyin.")
        pending = connection.execute("SELECT id FROM type_management_requests WHERE actor_id=? AND product=? AND status='pending'", (user.id, product)).fetchone()
        if pending:
            raise HTTPException(409, "Bu tip için bekleyen talebiniz var. Yönetici talepleri listesini açın.")
        connection.execute("INSERT INTO type_management_requests(id,actor_id,actor_name,product,reason,status,created_at) VALUES(?,?,?,?,?,'pending',?)",
            (payload.id, user.id, user.name, product, reason, store.now_iso()))
        return {"request": _view(_owned(connection, payload.id, user)), "replayed": False}


@router.get("/{identity}")
def inspect_type_request(identity: str, user: CurrentUser = Depends(current_user)):
    with store.connection() as connection:
        row = _owned(connection, identity, user)
        seed, revision = _state(connection)
        product = _product(seed, row["product"])
        blockers = product_type_deletion_blockers(seed, row["product"]) if product else ["Tip artık mevcut değil."]
        return {"request": _view(row), "worldRevision": revision, "blockers": blockers,
            "exists": product is not None, "canRetire": any(item.get("product") == row["product"] for item in seed.get("products", [])), "retired": bool(product and product.get("retired"))}


@router.post("/{identity}/review")
def review_type_request(identity: str, payload: ReviewTypeRequest, user: CurrentUser = Depends(require_admin)):
    note = payload.note.strip()
    if not note:
        raise HTTPException(422, "Yönetici kararının açıklamasını girin.")
    with store.connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        row = _owned(connection, identity, user)
        if row["status"] != "pending":
            if row["revision"] == payload.expectedRevision + 1 and (row["reviewer_id"], row["decision"], row["review_note"], row["review_basis"]) == (user.id, payload.decision, note, payload.expectedWorldRevision):
                return {"request": _view(row), "replayed": True}
            raise HTTPException(409, "Talep zaten sonuçlandı. Listeyi yenileyin.")
        seed, revision = _state(connection)
        if row["revision"] != payload.expectedRevision or revision != payload.expectedWorldRevision:
            raise HTTPException(409, "Talep veya ortak kayıt değişti. Güncel kullanımı yeniden inceleyin.")
        result_revision = revision
        if payload.decision != "reject":
            if _product(seed, row["product"]) is None:
                raise HTTPException(409, "Tip artık mevcut değil. Talebi yeniden inceleyin.")
            if payload.decision == "delete":
                try:
                    candidate = remove_unused_product_type(seed, row["product"])
                except ValueError as error:
                    raise HTTPException(422, str(error)) from error
            else:
                if not any(item.get("product") == row["product"] for item in seed.get("products", [])):
                    raise HTTPException(422, "Kullanım durumu için önce ürün parametrelerini tamamlayın.")
                candidate = deepcopy(seed)
                _product(candidate, row["product"])["retired"] = payload.decision == "retire"
                candidate["planNeedsRecalculation"] = True
                candidate.pop("lastAutomaticPlan", None)
                candidate.pop("planRunSequence", None)
            saved = store.save_planning_state(candidate, expected_updated_at=revision, actor_id=user.id, actor_name=user.name,
                can_manage_settings=True, flow_settings_version=1, route_placement_version=1, production_split_version=1,
                process_wait_settings_version=1, stock_planning_version=1, monthly_planning_version=1,
                internal_connection=connection, shared_inputs_only=True)
            result_revision = saved["updatedAt"]
        connection.execute("UPDATE type_management_requests SET status=?,revision=revision+1,reviewed_at=?,reviewer_id=?,reviewer_name=?,decision=?,review_note=?,result_revision=?,review_basis=? WHERE id=?",
            ("rejected" if payload.decision == "reject" else "approved", store.now_iso(), user.id, user.name, payload.decision, note, result_revision, payload.expectedWorldRevision, identity))
        return {"request": _view(_owned(connection, identity, user)), "replayed": False}
