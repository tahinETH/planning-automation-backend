from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone
from io import BytesIO
from copy import copy
from typing import Any, Literal

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill


DataPackageScope = Literal["parameters", "settings", "scenarios", "complete"]
MAX_DATA_PACKAGE_BYTES = 20 * 1024 * 1024
FORMAT_NAME = "SELSA_PLANLAMA_DATA_PACKAGE"
FORMAT_VERSION = 1
CHUNK_SIZE = 30_000

SCOPE_LABELS: dict[DataPackageScope, str] = {
    "parameters": "Parametreler",
    "settings": "Ayarlar",
    "scenarios": "Senaryolar",
    "complete": "Parametreler ve Ayarlar",
}


class DataPackageError(ValueError):
    pass


def _header(sheet, values: list[str]) -> None:
    sheet.append(values)
    fill = PatternFill("solid", fgColor="24443D")
    for cell in sheet[1]:
        cell.fill = fill
        cell.font = Font(color="FFFFFF", bold=True)
        cell.alignment = Alignment(vertical="center")
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions


def _append_rows(sheet, headers: list[str], rows: list[list[Any]]) -> None:
    _header(sheet, headers)
    for row in rows:
        sheet.append(row)
    for column in sheet.columns:
        width = min(45, max(10, max(len(str(cell.value or "")) for cell in column) + 2))
        sheet.column_dimensions[column[0].column_letter].width = width


def _parameter_sheets(workbook: Workbook, data: dict[str, Any]) -> None:
    products = data.get("products", [])
    parameter_sheet = workbook.create_sheet("Ürün Parametreleri")
    _append_rows(parameter_sheet, ["Ürün", "Ürün Ailesi", "Şarj Büyüklüğü", "Günlük Üretim", "Vardiya Üretimi", "Parametre Üretimi", "Çap", "Kaynak"], [
        [
            item.get("product", ""),
            {"piston": "Piston", "center-pin": "Center pim", "cubuk-filtre": "Çubuk Filtre"}.get(item.get("setupFamily"), "Tanımsız"),
            item.get("batchSize", 0),
            item.get("dailyRate", 0),
            item.get("shiftRate", 0),
            item.get("parameterDailyRate", 0),
            item.get("diameter", ""),
            item.get("source", ""),
        ]
        for item in products
    ])
    priority_sheet = workbook.create_sheet("Tezgah Öncelikleri")
    rows: list[list[Any]] = []
    machine_rates = {item.get("id"): item.get("rates", {}) for item in data.get("machineRates", [])}
    for product in products:
        machines = next((rule.get("machines", []) for rule in data.get("preferences", []) if rule.get("key") == product.get("product")), product.get("eligibleMachines", []))
        for index, machine_id in enumerate(machines):
            rows.append([product.get("product", ""), index + 1, machine_id, machine_rates.get(machine_id, {}).get(str(product.get("product", "")).upper(), "")])
    _append_rows(priority_sheet, ["Ürün", "Öncelik", "Tezgah", "Günlük Üretim"], rows)
    _process_parameter_sheet(workbook, data.get("processMasterData") or {})


PROCESS_LABELS = {"drilling": "Delme", "deburring": "Çapak Alma", "gkm": "GKM", "gtm": "GTM",
                  "diameter-grinding": "Çap Taşlama", "form-grinding": "Form Taşlama", "measuring": "Ölçme",
                  "milling": "Freze", "final-inspection": "Final Kontrol", "filter-visual": "Göz Kontrol"}


def _process_parameter_sheet(workbook: Workbook, master: dict[str, Any]) -> None:
    """Readable Delme and later rows; the hidden payload stays the import source."""
    resources = {item.get("id"): item for item in master.get("resources") or []}
    rows: list[list[Any]] = []
    for product in master.get("products") or []:
        for parameter in product.get("processes") or []:
            if parameter.get("process") == "turning":
                continue
            inactive = set(parameter.get("inactiveResourceIds") or [])
            for index, resource_id in enumerate(parameter.get("resourcePriority") or []):
                setup = (parameter.get("setupMinutesByResource") or {}).get(resource_id, "")
                rows.append([
                    product.get("product", ""), PROCESS_LABELS.get(parameter.get("process"), parameter.get("process")),
                    index + 1, resource_id, (resources.get(resource_id) or {}).get("name", ""),
                    "Pasif" if resource_id in inactive else "Aktif",
                    (parameter.get("unitsPerShift") or {}).get(resource_id, ""),
                    parameter.get("setupKey", ""), setup, parameter.get("waitWorkdaysBefore", 0),
                    product.get("productGroup", ""),
                ])
    sheet = workbook.create_sheet("Proses Parametreleri")
    _append_rows(sheet, ["Ürün", "Proses", "Öncelik", "İş merkezi", "İş merkezi adı", "Planlama durumu", "Adet / vardiya",
                         "Setup anahtarı", "Setup (dk)", "Bekleme (iş günü)", "Ürün grubu"], rows)


def _flow_settings_sheet(workbook: Workbook, flow: dict[str, Any] | None) -> None:
    sheet = workbook.create_sheet("Akış Ayarları")
    families = {"piston": "Piston", "center-pin": "Center Pin"}
    labels = {"turning": "Torna", "delivery": "Paketleme / Final Kontrol", **PROCESS_LABELS}
    rows: list[list[Any]] = [["Saat bazlı akış", "Açık" if (flow or {}).get("enabled") else "Kapalı", "", "", "", "", ""]]
    for rule in (flow or {}).get("rules") or []:
        minutes = rule.get("minutes", 0)
        rows.append([rule.get("description", ""), families.get(rule.get("family"), rule.get("family")),
                     f"{labels.get(rule.get('from'), rule.get('from'))} → {labels.get(rule.get('to'), rule.get('to'))}",
                     "Bitiş farkı hedefi" if rule.get("mode") == "dynamic" else "Sabit bekleme (çalışma saati)",
                     minutes, round(minutes / 60, 2) if isinstance(minutes, (int, float)) else "", "Aktif" if rule.get("active") else "Pasif"])
    _append_rows(sheet, ["Kural", "Aile", "Geçiş", "Tür", "Dakika", "Saat", "Durum"], rows)


def _settings_sheets(workbook: Workbook, data: dict[str, Any]) -> None:
    waits = workbook.create_sheet("Proses Bekleme Süreleri")
    _append_rows(waits, ["Proses", "Bekleme var", "Bekleme süresi (iş günü)"],
                 [[process, item.get("enabled", False), item.get("workdays", 0)]
                  for process, item in (data.get("processWaitSettings") or {}).items()])
    materials = data.get("rawMaterialSettings") or {}
    stocks = workbook.create_sheet("Hammadde Stokları")
    _append_rows(stocks, ["Hammadde kodu", "Ambar stoğu (kg)", "Güncelleme Tarihi"],
                 [[row.get("materialCode"), row.get("kg"), materials.get("stockDate", "")]
                  for row in materials.get("stocks", [])])
    weights = workbook.create_sheet("Ürün Ağırlıkları")
    _append_rows(weights, ["Tip no", "Ürün adı", "Hammadde kodu", "Hammadde açıklaması", "Hammadde ağırlığı (g)"],
                 [[row.get("product"), row.get("productName"), row.get("materialCode"), row.get("materialName"), row.get("grams")]
                  for row in data.get("productWeights", [])])
    setup = data.get("setupSettings", {}) or {}
    setup_sheet = workbook.create_sheet("Genel Ayarlar")
    _append_rows(setup_sheet, ["Ayar", "Değer"], [
        ["Iskarta Oranı (%)", materials.get("scrapPercent", 2)],
        ["Vardiya süresi (saat)", setup.get("shiftHours", "")],
        ["Aynı çap setup (saat)", setup.get("sameDiameterHours", "")],
        ["Aynı aile, farklı çap setup (saat)", setup.get("sameFamilyDifferentDiameterHours", "")],
        ["Piston - center pim geçişi (saat)", setup.get("crossFamilyHours", "")],
        ["Başlangıç / tanımsız aile setup (saat)", setup.get("differentDiameterHours", "")],
    ])
    holiday_sheet = workbook.create_sheet("Tatil Günleri")
    _append_rows(holiday_sheet, ["Tatil", "Excel Tarih Seri No", "Çalışılan Vardiya"], [
        [item.get("name", ""), item.get("serial", ""), item.get("workingShifts", 0)]
        for item in data.get("holidays", [])
    ])
    event_sheet = workbook.create_sheet("Tezgah Takvimi")
    _append_rows(event_sheet, ["Kayıt ID", "Tezgah", "Tür", "Açıklama", "Başlangıç", "Bitiş", "Vardiya"], [
        [item.get("id", ""), item.get("machineId", ""), item.get("kind", ""), item.get("name", ""), item.get("start", ""), item.get("end", ""), item.get("shiftCount", 0)]
        for item in data.get("calendarEvents", [])
    ])
    if data.get("flowSettings") is not None:
        _flow_settings_sheet(workbook, data.get("flowSettings"))
    machine_sheet = workbook.create_sheet("Tezgah Ayarları")
    _append_rows(machine_sheet, ["Tezgah", "Ad", "Aktif", "Müsait Başlangıç", "Plan Bitişi", "Vardiya", "Kapasite"], [
        [item.get("id", ""), item.get("name", ""), item.get("active", False), item.get("availableStart", ""), item.get("planEnd", ""), item.get("shiftFactor", 0), item.get("capacityFactor", 1)]
        for item in data.get("machines", [])
    ])


def _scenario_sheets(workbook: Workbook, data: Any) -> None:
    scenarios = data if isinstance(data, list) else data.get("scenarios", [])
    sheet = workbook.create_sheet("Senaryolar")
    _append_rows(sheet, ["Senaryo", "Açıklama", "Oluşturulma", "Talep", "Planlanan", "Şarj", "Plan Bitişi"], [
        [
            item.get("name", ""),
            item.get("notes", ""),
            item.get("createdAt", ""),
            item.get("result", {}).get("summary", {}).get("demand", 0),
            item.get("result", {}).get("summary", {}).get("planned", 0),
            item.get("result", {}).get("summary", {}).get("plannedBatchCount", 0),
            item.get("result", {}).get("summary", {}).get("completion", ""),
        ]
        for item in scenarios
    ])


PLAN_SHEETS = (("turning", "Torna Planı"), ("drilling", "Delme Planı"), ("deburring", "Çapak Alma Planı"), ("gkm", "GKM Planı"))
PLAN_HEADERS = ["Senaryo ID", "Senaryo adı", "Kayıt tarihi", "Şarj / iş ID", "İş emri", "Tip", "Adet", "Tezgah / iş merkezi",
                "Başlangıç", "Bitiş", "Hazır olma", "Setup (saat)", "Bekleme kuralı", "Kaynak türü", "Durum", "Not"]
DATE_FORMAT = "dd.mm.yyyy hh:mm"


def _excel_datetime(serial: Any) -> Any:
    """Factory wall-clock Excel serial → naive datetime (Türkiye saati).

    Non-numeric, non-finite, non-positive or out-of-range values (beyond the
    Excel date limit 31.12.9999) stay empty; the row status shows Tarihsiz.
    """
    if not isinstance(serial, (int, float)) or isinstance(serial, bool) or not math.isfinite(serial) or not 0 < serial < 2958466:
        return None
    try:
        return datetime(1899, 12, 30) + timedelta(days=float(serial))
    except (OverflowError, ValueError):
        return None


def _plain(value: Any, limit: int = 500) -> Any:
    """Cell-safe scalar: numbers stay numbers, everything else bounded text."""
    if isinstance(value, bool) or value is None:
        return "" if value is None else str(value)
    if isinstance(value, (int, float)):
        return value if math.isfinite(value) else ""
    return str(value)[:limit]


def _scenario_plan_sheets(workbook: Workbook, plans: dict[str, Any]) -> None:
    """Readable per-process plans from stored scenarios (server-computed)."""
    scenarios = plans.get("scenarios") or []

    def readable_layout(sheet, widths, freeze):
        sheet.freeze_panes = freeze
        sheet.auto_filter.ref = sheet.dimensions
        sheet.sheet_view.zoomScale = 85
        sheet.sheet_properties.pageSetUpPr.fitToPage = True
        sheet.page_setup.orientation = "landscape"
        sheet.page_setup.paperSize = sheet.PAPERSIZE_A3
        sheet.page_setup.fitToWidth = 1
        sheet.page_setup.fitToHeight = 0
        sheet.print_title_rows = "1:1"
        sheet.print_options.horizontalCentered = True
        sheet.row_dimensions[1].height = 36
        for index, width in enumerate(widths, 1):
            sheet.column_dimensions[sheet.cell(1, index).column_letter].width = width
        for row in sheet.iter_rows():
            lines = 1
            for cell in row:
                cell.alignment = Alignment(vertical="top", wrap_text=True)
                if cell.row == 1:
                    cell.font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
                else:
                    cell.font = Font(name="Calibri", size=10, color="243B35")
                    width = widths[cell.column - 1]
                    text = str(cell.value or "")
                    lines = max(lines, sum(max(1, math.ceil(len(part) / max(8, width - 2))) for part in text.split("\n")))
            if row[0].row > 1:
                sheet.row_dimensions[row[0].row].height = max(32, min(180, lines * 15 + 8))

    for key, title in PLAN_SHEETS:
        sheet = workbook.create_sheet(title)
        rows: list[list[Any]] = []
        for scenario in scenarios:
            identity = [_plain(scenario.get("id", "")), _plain(scenario.get("name", "")), _plain(scenario.get("createdAt", ""))]
            if scenario.get("status") != "ok":
                rows.append([*identity, "", "", "", "", "", None, None, None, None, "", "", "Plan yok", scenario.get("error") or "Plan hesaplanamadı."])
                continue
            items = (scenario.get("rows") or {}).get(key) or []
            if not isinstance(items, list):
                items = []
            if not items:
                rows.append([*identity, "", "", "", "", "", None, None, None, None, "", "", "Plan boş", "Bu senaryoda bu proseste iş yok."])
            for item in items:
                if not isinstance(item, dict):
                    continue
                setup = item.get("setupHours")
                start, end = _excel_datetime(item.get("start")), _excel_datetime(item.get("end"))
                status = _plain(item.get("status", ""))
                if status == "Planlandı" and (start is None or end is None):
                    status = "Tarihsiz"
                rows.append([*identity, _plain(item.get("id", "")), _plain(item.get("workOrder", "")), _plain(item.get("product", "")), _plain(item.get("quantity", 0)), _plain(item.get("resourceId", "")),
                             start, end, _excel_datetime(item.get("readyAt")),
                             round(setup, 3) if isinstance(setup, (int, float)) and not isinstance(setup, bool) and math.isfinite(setup) else None,
                             _plain(item.get("wait", "")), _plain(item.get("source", "")), status, _plain(item.get("note", ""))])
        if not scenarios:
            rows.append(["", "", "", "", "", "", "", "", None, None, None, None, "", "", "Plan yok", "Seçili senaryo yok."])
        _append_rows(sheet, PLAN_HEADERS, rows)
        readable_layout(sheet, [18, 26, 27, 30, 24, 18, 12, 23, 23, 23, 23, 15, 34, 24, 19, 65], "C2")
        for row in sheet.iter_rows(min_row=2, min_col=7, max_col=7):
            row[0].number_format = "#,##0"
        for row in sheet.iter_rows(min_row=2, min_col=12, max_col=12):
            row[0].number_format = "0.###"
        for row in sheet.iter_rows(min_row=2, min_col=9, max_col=11):
            for cell in row:
                if cell.value is not None:
                    cell.number_format = DATE_FORMAT
    warnings = workbook.create_sheet("Plan Uyarıları")
    warning_rows = [[scenario.get("id", ""), scenario.get("name", ""), item.get("code", ""), item.get("product", ""), item.get("batchId", ""), item.get("message", "")]
                    for scenario in scenarios for item in scenario.get("warnings") or []]
    warning_rows += [[scenario.get("id", ""), scenario.get("name", ""), scenario.get("status", ""), "", "", scenario.get("error", "")]
                     for scenario in scenarios if scenario.get("status") != "ok"]
    if plans.get("error"):
        warning_rows.append(["", "", "plan-error", "", "", plans["error"]])
    if not warning_rows:
        warning_rows.append(["", "", "", "", "", "Uyarı yok."])
    _append_rows(warnings, ["Senaryo ID", "Senaryo adı", "Kod", "Tip", "Şarj / iş ID", "Açıklama"], warning_rows)
    readable_layout(warnings, [18, 28, 26, 18, 32, 110], "C2")


def _literal_text_cells(workbook: Workbook) -> None:
    """Formula-injection safety: every cell text stays literal text, never a formula.

    Data packages contain no intended formulas. A string starting with "=" is
    stored as a text cell (value unchanged), including hidden payload chunks.
    """
    for sheet in workbook.worksheets:
        for row in sheet.iter_rows():
            for cell in row:
                if cell.data_type == "f":
                    cell.data_type = "s"


def build_data_package(scope: DataPackageScope, data: Any, plans: dict[str, Any] | None = None) -> bytes:
    workbook = Workbook()
    info = workbook.active
    info.title = "Bilgi"
    info.append(["Selsa Planlama Excel Veri Paketi"])
    info["A1"].font = Font(size=16, bold=True, color="24443D")
    info.append(["Kapsam", SCOPE_LABELS[scope]])
    if isinstance(data, dict) and data.get("productionArea") == "cubuk-filtre":
        info.append(["Üretim alanı", "Çubuk Filtre"])
    info.append(["Format sürümü", FORMAT_VERSION])
    info.append(["Oluşturulma", datetime.now(timezone.utc).isoformat()])
    info.append(["Not", "Bu dosya Selsa Planlama uygulamasına tekrar yüklenebilir. Gizli veri sayfasını silmeyin."])
    info.column_dimensions["A"].width = 24
    info.column_dimensions["B"].width = 72

    is_filter = False
    if scope == "parameters":
        _parameter_sheets(workbook, data)
    elif scope == "complete":
        # One workbook: parameter and settings sections keep their own sheets.
        if not isinstance(data, dict) or not isinstance(data.get("parameters"), dict) or not isinstance(data.get("settings"), dict):
            raise DataPackageError("Tam yedek paketinde Parametreler ve Ayarlar bölümleri gereklidir.")
        _parameter_sheets(workbook, data["parameters"])
        _settings_sheets(workbook, data["settings"])
    elif scope == "settings":
        _settings_sheets(workbook, data)
    else:
        _scenario_sheets(workbook, data)
        from .production_area import production_area
        is_filter = production_area.get() == "cubuk-filtre" or (isinstance(data, list) and any(isinstance(item, dict) and isinstance(item.get("seed"), dict) and item["seed"].get("productionArea") == "cubuk-filtre" for item in data))
    if scope == "scenarios" and not is_filter:
        # Çubuk Filtre export is unchanged (deferred scope): no Piston plan sheets.
        if plans is None:
            from .database import scenario_record
            from .scenario_plans import scenario_plans
            requested = data if isinstance(data, list) else (data.get("scenarios", []) if isinstance(data, dict) else [])
            plans = scenario_plans(requested, scenario_record)
        engine = plans.get("engine")
        info.append(["Plan sayfaları", "Tarihler sunucuda kayıtlı senaryo girdisinden paylaşılan rota motoruyla hesaplandı. Tarayıcıdaki tarihler kullanılmadı."])
        info.append(["Plan motoru", f"Motor SHA-256 {engine}" if engine else "Motor hazır değil; plan hesaplanmadı"])
        info.append(["Plan hesap zamanı (UTC)", plans.get("computedAt", "")])
        info.append(["Plan saat dilimi", "Türkiye (fabrika saati); süreler saat; bekleme iş günü veya çalışma saati olarak yazılır"])
        if plans.get("error"):
            info.append(["Plan uyarısı", plans["error"]])
        # Format only the Piston scenario views; hidden backup and CF stay unchanged.
        summary = workbook["Senaryolar"]
        summary.cell(1, 8, "Senaryo ID")
        summary.cell(1, 8)._style = copy(summary.cell(1, 1)._style)
        requested = data if isinstance(data, list) else data.get("scenarios", [])
        for index, scenario in enumerate(requested, 2):
            summary.cell(index, 8, _plain(scenario.get("id", "")))
        summary.freeze_panes = "B2"
        summary.auto_filter.ref = summary.dimensions
        summary.row_dimensions[1].height = 32
        for column, width in {"A": 30, "B": 72, "C": 28, "D": 16, "E": 16, "F": 12, "G": 22, "H": 20}.items():
            summary.column_dimensions[column].width = width
        for row in summary.iter_rows():
            for cell in row:
                cell.alignment = Alignment(vertical="top", wrap_text=True)
            if row[0].row > 1:
                summary.row_dimensions[row[0].row].height = max(32, min(150, math.ceil(len(str(row[1].value or "")) / 68) * 15 + 8))
        info.merge_cells("A1:B1")
        info.column_dimensions["A"].width = 30
        info.column_dimensions["B"].width = 112
        info.row_dimensions[1].height = 28
        info.freeze_panes = "B2"
        for row in info.iter_rows():
            for cell in row:
                cell.alignment = Alignment(vertical="top", wrap_text=True)
                if cell.row > 1:
                    cell.font = Font(name="Calibri", size=11, color="243B35")
            if row[0].row > 1:
                text = str(row[1].value or "") if len(row) > 1 else ""
                info.row_dimensions[row[0].row].height = max(32, math.ceil(len(text) / 105) * 16 + 10)
        try:
            _scenario_plan_sheets(workbook, plans)
        except Exception:
            # Malformed stored data must not fail the export: keep empty sheets
            # with headers and an explicit warning instead of partial rows.
            for title in [title for _, title in PLAN_SHEETS] + ["Plan Uyarıları"]:
                if title in workbook.sheetnames:
                    del workbook[title]
            _scenario_plan_sheets(workbook, {"scenarios": [], "error": "Plan sayfaları kayıtlı senaryo verisinden oluşturulamadı; plan gösterilmedi."})

    payload = json.dumps({"format": FORMAT_NAME, "version": FORMAT_VERSION, "scope": scope, "data": data}, ensure_ascii=False, separators=(",", ":"))
    storage = workbook.create_sheet("__SelsaVeri")
    storage.append(["Sıra", "Veri"])
    for index in range(0, len(payload), CHUNK_SIZE):
        storage.append([index // CHUNK_SIZE + 1, payload[index:index + CHUNK_SIZE]])
    storage.sheet_state = "veryHidden"

    _literal_text_cells(workbook)
    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def parse_data_package(content: bytes, expected_scope: DataPackageScope) -> Any:
    if not content:
        raise DataPackageError("Excel dosyası boş.")
    if len(content) > MAX_DATA_PACKAGE_BYTES:
        raise DataPackageError("Excel veri paketi 20 MB sınırını aşıyor.")
    try:
        workbook = load_workbook(BytesIO(content), read_only=True, data_only=True)
    except Exception:
        raise DataPackageError("Dosya geçerli bir .xlsx çalışma kitabı değil.") from None
    if "__SelsaVeri" not in workbook.sheetnames:
        raise DataPackageError("Bu dosya Selsa Planlama tarafından oluşturulmuş bir veri paketi değil.")
    rows = list(workbook["__SelsaVeri"].iter_rows(min_row=2, values_only=True))
    chunks = [(int(row[0]), str(row[1] or "")) for row in rows if row[0] is not None]
    if not chunks:
        raise DataPackageError("Excel veri paketindeki uygulama verisi bulunamadı.")
    try:
        payload = json.loads("".join(value for _, value in sorted(chunks)))
    except (TypeError, ValueError):
        raise DataPackageError("Excel veri paketindeki uygulama verisi okunamadı.") from None
    if payload.get("format") != FORMAT_NAME or payload.get("version") != FORMAT_VERSION:
        raise DataPackageError("Excel veri paketinin sürümü desteklenmiyor.")
    if payload.get("scope") != expected_scope:
        raise DataPackageError(f"Bu dosya {SCOPE_LABELS[expected_scope]} alanına ait değil.")
    return payload.get("data")
