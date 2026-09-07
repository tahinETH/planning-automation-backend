"""One-time, reviewed raw-material weights from the supplied workbook (grams)."""
import json
import math
from copy import deepcopy
from pathlib import Path


def initial_product_weights() -> list[dict]:
    return json.loads(Path(__file__).with_name("product-weights.json").read_text())["rows"]


def validate_product_weights(rows: object) -> None:
    if not isinstance(rows, list) or len(rows) > 5000:
        raise ValueError("Ürün ağırlıkları listesi geçersiz.")
    codes = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Ürün ağırlığı kaydı geçersiz.")
        code, grams = row.get("product"), row.get("grams")
        if (not isinstance(code, str) or not code.strip() or code != code.strip().upper() or code in codes
                or any(not isinstance(row.get(key), str) for key in ("productName", "materialCode", "materialName"))
                or (grams is not None and (isinstance(grams, bool) or not isinstance(grams, (int, float)) or not math.isfinite(grams) or grams <= 0))):
            raise ValueError("Ürün kodları benzersiz, ağırlıklar sıfırdan büyük olmalıdır. Bilinmeyen ağırlığı boş bırakın.")
        codes.add(code)


def preserve_missing_weights(incoming: dict, current: dict | None) -> dict:
    # Older clients/packages must not erase administrator-maintained weights.
    if "productWeights" not in incoming and current and "productWeights" in current:
        return {**incoming, "productWeights": deepcopy(current["productWeights"])}
    return incoming
