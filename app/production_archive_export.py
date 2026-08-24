from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter


NAVY = "315C9B"
NAVY_LIGHT = "E8EEF7"
GREEN = "1E7B57"
INK = "18201D"
MUTED = "6C756F"
LINE = "DDE2DC"
PAPER = "F7F8F5"
WHITE = "FFFFFF"


def _fill(color: str) -> PatternFill:
    return PatternFill("solid", fgColor=color)


def _status_label(status: str) -> str:
    return "Yarı mamuller" if status == "semi-finished" else "Iskartalar" if status == "scrapped" else "Teslim edilenler"


def _sheet_title(status: str) -> str:
    return "WIP - Yarı Mamul" if status == "semi-finished" else "Iskarta" if status == "scrapped" else "Teslim Edilen"


def _row_quantity(row: dict[str, Any], quantity_key: str) -> int:
    value = row.get(quantity_key)
    return max(0, int(row.get("completedQuantity", 0) if value is None else value))


def _build_archive_sheet(workbook: Workbook, section: dict[str, Any], payload: dict[str, Any], *, first: bool) -> None:
    status = section.get("status", "semi-finished")
    rows = section.get("rows", [])
    sheet = workbook.active if first else workbook.create_sheet()
    sheet.title = _sheet_title(status)
    sheet.sheet_view.showGridLines = False
    sheet.freeze_panes = "A9"
    sheet.page_setup.orientation = "landscape"
    sheet.page_setup.fitToWidth = 1
    sheet.sheet_properties.pageSetUpPr.fitToPage = True

    generated_at = payload.get("generatedAt") or datetime.now(timezone.utc).isoformat()
    quantity_key = "availableQuantity" if status == "semi-finished" else "completedQuantity"
    total_quantity = sum(_row_quantity(row, quantity_key) for row in rows)
    machine_count = len({row.get("machineId") for row in rows if row.get("machineId")})

    sheet.merge_cells("A1:N2")
    title = sheet["A1"]
    title.value = f"SELSA  ·  ÜRETİM ARŞİVİ  ·  {_status_label(status).upper()}"
    title.fill = _fill(NAVY)
    title.font = Font(name="Aptos Display", size=18, color=WHITE, bold=True)
    title.alignment = Alignment(vertical="center")
    for row in sheet["A1:N2"]:
        for cell in row:
            cell.fill = _fill(NAVY)

    sheet.merge_cells("A3:G3")
    sheet["A3"] = f"Durum: {_status_label(status)}"
    sheet["A3"].font = Font(name="Aptos", size=9, color=GREEN, bold=True)
    sheet.merge_cells("H3:N3")
    sheet["H3"] = f"Oluşturulma: {generated_at}"
    sheet["H3"].font = Font(name="Aptos", size=8, color=MUTED)
    sheet["H3"].alignment = Alignment(horizontal="right")

    metrics = [
        ("KAYIT", len(rows), "görünen satır"),
        ("TOPLAM ISKARTA" if status == "scrapped" else "WIP MİKTARI" if status == "semi-finished" else "TESLİM EDİLEN", total_quantity, "adet"),
        ("TEZGAH", machine_count, "farklı tezgah"),
        ("KAPSAM", "Filtreli" if payload.get("filtered") else "Tümü", f"{section.get('totalAvailable', len(rows))} kayıt içinde"),
    ]
    metric_ranges = [(1, 2), (3, 4), (5, 6), (7, 14)]
    for index, ((label, value, detail), (start_col, end_col)) in enumerate(zip(metrics, metric_ranges, strict=True)):
        start = get_column_letter(start_col)
        end = get_column_letter(end_col)
        for row_number, content in ((5, label), (6, value), (7, detail)):
            sheet.merge_cells(f"{start}{row_number}:{end}{row_number}")
            sheet[f"{start}{row_number}"] = content
        sheet[f"{start}5"].fill = _fill(NAVY_LIGHT)
        sheet[f"{start}5"].font = Font(name="Aptos", size=8, color=MUTED, bold=True)
        sheet[f"{start}6"].font = Font(name="Aptos Display", size=16, color=GREEN if index < 3 else NAVY, bold=True)
        sheet[f"{start}7"].font = Font(name="Aptos", size=7, color=MUTED)
        if isinstance(value, (int, float)):
            sheet[f"{start}6"].number_format = "#,##0"

    headings = [
        str(section.get("eventDateLabel") or "Tamamlanma"), "Tezgah", "Tezgah adı", "Şarj / iş emri",
        "Ürün", "Ürün ailesi", "Son tamamlanan", "Güncel aşama", "Çalışan proses", "Sıradaki proses",
        "WIP miktarı" if status == "semi-finished" else "Iskarta" if status == "scrapped" else "Teslim edilen",
        "Planlanan başlangıç", "Planlanan bitiş", "Teslim tarihi",
    ]
    widths = [16, 12, 24, 18, 20, 15, 17, 24, 20, 18, 14, 20, 20, 16]
    thin = Side(style="thin", color=LINE)
    for column, (heading, width) in enumerate(zip(headings, widths, strict=True), 1):
        cell = sheet.cell(9, column, heading)
        cell.fill = _fill(NAVY)
        cell.font = Font(name="Aptos", size=8, color=WHITE, bold=True)
        cell.alignment = Alignment(vertical="center", horizontal="right" if column == 11 else "left")
        cell.border = Border(bottom=thin)
        sheet.column_dimensions[get_column_letter(column)].width = width

    process_labels = {"turning": "Torna", "drilling": "Delme", "deburring": "Çapak alma", "washing": "Yıkama", "gkm": "GKM"}
    family_labels = {"piston": "Piston", "center-pin": "Center pim"}
    for row_index, item in enumerate(rows, 10):
        values = [
            item.get("completedAt", ""), item.get("machineId", ""), item.get("machineName", ""), item.get("workOrder", ""),
            item.get("product", ""), family_labels.get(item.get("setupFamily"), "Aile tanımsız"),
            process_labels.get(item.get("process"), item.get("process", "")), item.get("stage", ""),
            item.get("currentOperation", ""), item.get("nextOperation", ""),
            _row_quantity(item, quantity_key),
            item.get("plannedStart", ""), item.get("plannedEnd", ""), item.get("deliveryDate", ""),
        ]
        for column, value in enumerate(values, 1):
            cell = sheet.cell(row_index, column, value)
            cell.fill = _fill(WHITE if row_index % 2 == 0 else PAPER)
            cell.font = Font(name="Aptos", size=8, color=INK, bold=column in {2, 4, 5})
            cell.alignment = Alignment(vertical="center", horizontal="right" if column == 11 else "left")
            cell.border = Border(bottom=thin)
            if column == 11:
                cell.number_format = "#,##0"

    last_row = max(9, sheet.max_row)
    sheet.auto_filter.ref = f"A9:N{last_row}"
    sheet.row_dimensions[1].height = 25
    sheet.row_dimensions[9].height = 25
    sheet.print_area = f"A1:N{last_row}"


def build_production_archive_workbook(payload: dict[str, Any]) -> bytes:
    workbook = Workbook()
    sections = payload.get("sections")
    if not isinstance(sections, list) or not sections:
        sections = [{
            "status": payload.get("status", "semi-finished"),
            "eventDateLabel": payload.get("eventDateLabel", "Tamamlanma"),
            "totalAvailable": payload.get("totalAvailable", len(payload.get("rows", []))),
            "rows": payload.get("rows", []),
        }]
    for index, section in enumerate(sections):
        _build_archive_sheet(workbook, section, payload, first=index == 0)

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()
