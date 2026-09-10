"""Validation of shared manual CPM stock snapshots; no server forecast engine."""
from datetime import date
import math


def initial_raw_material_settings() -> dict:
    return {"scrapPercent": 2, "stockDate": "", "stocks": []}


def validate_raw_material_settings(value: object) -> None:
    if not isinstance(value, dict):
        raise ValueError("Hammadde bilgileri geçersiz.")
    rate, stock_date, stocks = value.get("scrapPercent"), value.get("stockDate"), value.get("stocks")
    if (isinstance(rate, bool) or not isinstance(rate, (int, float)) or not math.isfinite(rate)
            or not 0 <= rate <= 100 or not isinstance(stock_date, str)
            or not isinstance(stocks, list) or len(stocks) > 5000):
        raise ValueError("Iskarta oranı 0–100 arasında ve stok listesi geçerli olmalıdır.")
    if stock_date:
        try:
            if date.fromisoformat(stock_date).isoformat() != stock_date:
                raise ValueError()
        except ValueError:
            raise ValueError("Güncelleme tarihi geçersiz.") from None
    codes = set()
    for row in stocks:
        if not isinstance(row, dict):
            raise ValueError("Hammadde stok kaydı geçersiz.")
        code, kg = row.get("materialCode"), row.get("kg")
        if (not isinstance(code, str) or not code.strip() or code != code.strip().upper() or code in codes
                or "kg" not in row or (kg is not None and (isinstance(kg, bool) or not isinstance(kg, (int, float))
                or not math.isfinite(kg) or kg < 0))):
            raise ValueError("Hammadde kodları benzersiz, stoklar sıfır veya pozitif kg olmalıdır.")
        codes.add(code)
