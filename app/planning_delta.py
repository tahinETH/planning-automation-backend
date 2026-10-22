"""Versioned state transport. Business validation stays in save_planning_state."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import re


MAX_PATCH_BYTES = 6 * 1024 * 1024
MAX_PATCH_ITEMS = 10000


def state_hash(seed: dict) -> str:
    return hashlib.sha256(json.dumps(seed, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _field(value: str) -> bool:
    return (isinstance(value, str) and bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,99}", value))
            and value not in {"constructor", "prototype"})


def _records(value) -> dict:
    if not isinstance(value, list) or any(not isinstance(row, dict) or not isinstance(row.get("id"), str)
                                          or not row["id"] for row in value):
        raise ValueError("Kayıt farkındaki liste kimlikleri geçerli olmalıdır.")
    rows = {row["id"]: row for row in value}
    if len(rows) != len(value):
        raise ValueError("Kayıt farkında aynı kimlik birden çok kez kullanılamaz.")
    return rows


def apply_delta(base: dict, delta: dict) -> dict:
    """Apply transport changes to a clone. Do not infer identities or business facts."""
    if not isinstance(delta, dict) or set(delta) != {"set", "remove", "arrays"}:
        raise ValueError("Kayıt farkı biçimi geçersiz.")
    fields, removed, arrays = delta["set"], delta["remove"], delta["arrays"]
    if not isinstance(fields, dict) or not isinstance(removed, list) or not isinstance(arrays, dict):
        raise ValueError("Kayıt farkı biçimi geçersiz.")
    names = [*fields, *removed, *arrays]
    if len(names) > 200 or any(not _field(name) for name in names) or len(set(names)) != len(names):
        raise ValueError("Kayıt farkı alanları geçersiz veya tekrarlı.")
    result = deepcopy(base)
    for name in removed:
        if name not in result:
            raise ValueError("Kaldırılacak kayıt alanı ortak sürümde yok.")
        del result[name]
    result.update(deepcopy(fields))
    item_count = len(names)
    for name, change in arrays.items():
        if not isinstance(change, dict) or set(change) - {"upsert", "remove", "order"} or not {"upsert", "remove"} <= set(change):
            raise ValueError("Liste farkı biçimi geçersiz.")
        current = _records(base.get(name))
        upsert = _records(change["upsert"])
        deletes = change["remove"]
        if (not isinstance(deletes, list) or any(not isinstance(key, str) or not key for key in deletes)
                or len(set(deletes)) != len(deletes) or set(deletes) & set(upsert)
                or any(key not in current for key in deletes)):
            raise ValueError("Silinecek liste kimlikleri geçersiz.")
        item_count += len(upsert) + len(deletes)
        for key in deletes:
            del current[key]
        current.update(deepcopy(upsert))
        if "order" in change:
            order = change["order"]
            if (not isinstance(order, list) or any(not isinstance(key, str) for key in order)
                    or len(order) != len(current) or len(set(order)) != len(order) or set(order) != set(current)):
                raise ValueError("Liste sırası tüm kayıt kimliklerini tam bir kez içermelidir.")
            item_count += len(order)
        else:
            order = list(current)
        result[name] = [current[key] for key in order]
    if item_count > MAX_PATCH_ITEMS:
        raise ValueError("Kayıt farkı işlem sınırını aşıyor. Yerel kopyayı koruyun.")
    # Also reject nonfinite JSON before any database mutation.
    if len(json.dumps(delta, ensure_ascii=False, allow_nan=False).encode()) > MAX_PATCH_BYTES:
        raise ValueError("Kayıt farkı boyut sınırını aşıyor. Yerel kopyayı koruyun.")
    return result


def build_delta(before: dict, after: dict) -> dict:
    """Encode server validation corrections. This does not calculate production."""
    delta = {"set": {}, "remove": [key for key in before if key not in after], "arrays": {}}
    encode = lambda value: json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    for key, value in after.items():
        if key in before and encode(before[key]) == encode(value):
            continue
        try:
            old_rows, new_rows = _records(before.get(key)), _records(value)
        except ValueError:
            delta["set"][key] = deepcopy(value)
            continue
        upsert = [deepcopy(row) for id_, row in new_rows.items() if id_ not in old_rows or encode(old_rows[id_]) != encode(row)]
        removed = [id_ for id_ in old_rows if id_ not in new_rows]
        natural = [id_ for id_ in old_rows if id_ in new_rows] + [id_ for id_ in new_rows if id_ not in old_rows]
        change = {"upsert": upsert, "remove": removed}
        if natural != list(new_rows):
            change["order"] = list(new_rows)
        delta["arrays"][key] = change
    return delta
