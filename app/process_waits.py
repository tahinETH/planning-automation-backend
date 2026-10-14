"""Validate administrator process wait settings before any write."""
PROCESSES = ("turning", "drilling", "deburring", "gkm")


def validate_process_wait_settings(value):
    message = "Bekleme süreleri 0–365 tam iş günü olmalı. Her proses için bekleme seçimi gereklidir."
    if not isinstance(value, dict) or set(value) != set(PROCESSES):
        raise ValueError(message)
    for item in value.values():
        if not isinstance(item, dict) or type(item.get("enabled")) is not bool or type(item.get("workdays")) is not int or not 0 <= item["workdays"] <= 365:
            raise ValueError(message)
