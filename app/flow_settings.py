"""Validate persisted flow inputs. Scheduling stays in the shared TS runtime."""
import math


def validate_flow_settings(value):
    def fail():
        raise ValueError("Akış ayarları geçersiz; süre, vardiya ve geçiş kurallarını kontrol edin.")

    def number(v, maximum, integer=False):
        return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) and 0 <= v <= maximum and (not integer or int(v) == v)

    if not isinstance(value, dict) or value.get("version") != 1 or value.get("department") != "piston" or not isinstance(value.get("enabled"), bool) or not number(value.get("defaultShifts"), 3, True):
        fail()
    rules, overrides = value.get("rules"), value.get("shiftOverrides")
    if not isinstance(rules, list) or len(rules) > 100 or not isinstance(overrides, list) or len(overrides) > 3660:
        fail()
    dates = set()
    for item in overrides:
        if not isinstance(item, dict) or not number(item.get("date"), 2958465, True) or item["date"] == 0 or not number(item.get("shifts"), 3, True) or item["date"] in dates:
            fail()
        dates.add(item["date"])
    ids, transitions = set(), set()
    order = ["turning", "drilling", "deburring", "gkm", "delivery"]
    for rule in rules:
        if not isinstance(rule, dict):
            fail()
        if not isinstance(rule.get("id"), str) or not rule["id"].strip() or rule["id"] in ids or rule.get("family") not in ("piston", "center-pin") or rule.get("mode") not in ("dynamic", "static") or not isinstance(rule.get("active"), bool) or not isinstance(rule.get("description"), str) or len(rule["description"]) > 500 or not number(rule.get("minutes"), 10080):
            fail()
        if rule.get("from") not in order[:-1] or rule.get("to") not in order[1:] or order.index(rule["from"]) >= order.index(rule["to"]) or rule["to"] == "delivery" and rule["mode"] != "static":
            fail()
        key = (rule["family"], rule["from"], rule["to"])
        if rule["active"] and key in transitions:
            fail()
        if rule["active"]:
            transitions.add(key)
        ids.add(rule["id"])
    setups = value.get("setupMinutes")
    if not isinstance(setups, dict):
        fail()
    for process in ("drilling", "deburring", "gkm"):
        setup = setups.get(process)
        if not isinstance(setup, dict) or not all(number(setup.get(key), 10080) for key in ("first", "sameProduct", "sameKey", "differentKey", "differentFamily")):
            fail()
    return value
