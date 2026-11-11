"""Editable assignment rates, priority and active state; separate from backup restore."""
from copy import deepcopy
from io import BytesIO
import math

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from openpyxl import load_workbook

from .auth import CurrentUser, current_user
from .data_package import build_data_package, parse_data_package, DataPackageError, MAX_DATA_PACKAGE_BYTES, _append_rows
from .models import DataPackagePayload
from .production_area import production_area

router = APIRouter(prefix="/api/parameter-sheet", tags=["parameters"])
SHEET = "Düzenlenebilir Hızlar"
HEADERS = ["Ürün", "Proses kodu", "Tezgah", "Öncelik", "Durum", "Adet / vardiya"]


def assignment_rows(data):
    rates = {row["id"]: row.get("rates", {}) for row in data.get("machineRates", [])}
    rows = []
    for product in data.get("products", []):
        code = product["product"]
        machines = next((rule["machines"] for rule in data.get("preferences", []) if rule.get("key") == code), product.get("eligibleMachines", product.get("alternativeMachines", [])))
        for rank, machine in enumerate(machines, 1):
            rows.append([code, "turning", machine, rank, "Pasif" if machine in product.get("inactiveMachineIds", []) else "Aktif", rates.get(machine, {}).get(code, 0)])
    for product in (data.get("processMasterData") or {}).get("products", []):
        for process in product.get("processes", []):
            if process["process"] == "turning":
                continue
            for rank, resource in enumerate(process.get("resourcePriority", []), 1):
                rows.append([product["product"], process["process"], resource, rank, "Pasif" if resource in process.get("inactiveResourceIds", []) else "Aktif", process.get("unitsPerShift", {}).get(resource, 0)])
    return rows


def build_parameter_sheet(data):
    workbook = load_workbook(BytesIO(build_data_package("parameters", data)))
    sheet = workbook.create_sheet(SHEET, 0)
    _append_rows(sheet, HEADERS, assignment_rows(data))
    for row in sheet:
        for cell in row:
            if isinstance(cell.value, str):
                cell.data_type = "s"
    workbook.active = 0
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def parse_parameter_sheet(content, admin=False):
    base = parse_data_package(content, "parameters")
    if base.get("productionArea", "torna") != production_area.get():
        raise DataPackageError("Dosya başka bir üretim alanına ait.")
    workbook = load_workbook(BytesIO(content), read_only=True, data_only=False)
    try:
        if SHEET not in workbook.sheetnames:
            raise DataPackageError("Düzenlenebilir parametre şablonunu kullanın.")
        sheet = workbook[SHEET]
        if sheet.max_row > 50001 or sheet.max_column != len(HEADERS):
            raise DataPackageError("Parametre tablosu en çok 50.000 satır ve altı sütun içerebilir.")
        values = sheet.iter_rows(values_only=True)
        if list(next(values, [])) != HEADERS:
            raise DataPackageError("Parametre sütun başlıklarını değiştirmeyin.")
        original = {tuple(row[:3]): row for row in assignment_rows(base)}
        rows = {}
        for line, raw in enumerate(values, 2):
            if all(value is None for value in raw):
                continue
            row = list(raw)
            key = tuple(row[:3])
            if key not in original or key in rows:
                raise DataPackageError(f"Satır {line}: ürün, proses ve tezgah kimliğini değiştirmeyin veya çoğaltmayın.")
            priority, status, rate = row[3:]
            if isinstance(priority, bool) or not isinstance(priority, (int, float)) or not math.isfinite(priority) or priority < 1 or priority != int(priority):
                raise DataPackageError(f"Satır {line}: öncelik pozitif tam sayı olmalıdır.")
            if status not in ("Aktif", "Pasif") or isinstance(rate, bool) or not isinstance(rate, (int, float)) or not math.isfinite(rate) or not 0 <= rate <= 1_000_000_000:
                raise DataPackageError(f"Satır {line}: durum Aktif/Pasif, hız 0–1.000.000.000 adet/vardiya olmalıdır. Formül kullanmayın.")
            if not admin and key[1] != "turning" and row != original[key]:
                raise DataPackageError("Torna dışındaki proses parametrelerini yalnız yönetici değiştirebilir.")
            rows[key] = row
        if rows.keys() != original.keys():
            raise DataPackageError("Atama satırı silinemez. Kullanılmayacak atamayı Pasif yapın.")
        groups = {}
        for row in rows.values():
            groups.setdefault(tuple(row[:2]), []).append(row)
        data = deepcopy(base)
        changes = []
        for (code, process), group in groups.items():
            group.sort(key=lambda row: row[3])
            if [row[3] for row in group] != list(range(1, len(group) + 1)):
                raise DataPackageError(f"{code} / {process}: öncelikler 1'den başlayıp tekrarsız ilerlemelidir.")
            changed = [row for row in group if row != original[tuple(row[:3])]]
            if not changed:
                continue
            changes.extend({"product": row[0], "process": row[1], "resource": row[2], "before": original[tuple(row[:3])][3:], "after": row[3:]} for row in changed)
            ids = [row[2] for row in group]
            inactive = [row[2] for row in group if row[4] == "Pasif"]
            if process == "turning":
                product = next(row for row in data["products"] if row["product"] == code)
                product.update(eligibleMachines=ids, alternativeMachines=ids, generalMachine=ids[0], inactiveMachineIds=inactive)
                preference = next((row for row in data["preferences"] if row["key"] == code), None)
                if preference is None:
                    data["preferences"].append({"key": code, "machines": ids, "ruleType": "Ürün parametresi", "description": "Excel şablonundaki tezgah sırası", "source": "Web Parametreleri"})
                else:
                    preference["machines"] = ids
                for row in group:
                    next(machine for machine in data["machineRates"] if machine["id"] == row[2])["rates"][code] = row[5]
            else:
                product = next(row for row in data["processMasterData"]["products"] if row["product"] == code)
                parameter = next(row for row in product["processes"] if row["process"] == process)
                parameter.update(resourcePriority=ids, inactiveResourceIds=inactive)
                parameter.setdefault("unitsPerShift", {}).update({row[2]: row[5] for row in group})
        return {"base": base, "data": data, "changes": changes}
    finally:
        workbook.close()


@router.post("/export")
def export_sheet(payload: DataPackagePayload, _: CurrentUser = Depends(current_user)):
    if payload.scope != "parameters" or not isinstance(payload.data, dict) or payload.data.get("productionArea", "torna") != production_area.get():
        raise HTTPException(422, "Bu alanın parametrelerini seçin.")
    return Response(build_parameter_sheet(payload.data), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": 'attachment; filename="Selsa_Parametre_Duzenleme.xlsx"'})


@router.post("/import")
async def import_sheet(file: UploadFile = File(...), user: CurrentUser = Depends(current_user)):
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(422, "Bir .xlsx şablonu seçin.")
    content = await file.read(MAX_DATA_PACKAGE_BYTES + 1)
    try:
        return parse_parameter_sheet(content, user.is_admin)
    except (DataPackageError, ValueError, KeyError, TypeError) as error:
        raise HTTPException(422, str(error)) from error
