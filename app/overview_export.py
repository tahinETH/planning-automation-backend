from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
from typing import Any

from openpyxl import Workbook
from openpyxl.worksheet.pagebreak import Break
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter


NAVY = "315C9B"
NAVY_LIGHT = "E8EEF7"
PEACH = "F1D0BC"
GREEN = "1E7B57"
GREEN_LIGHT = "E4F5E4"
ORANGE_LIGHT = "FFF0E9"
RED = "C84C43"
RED_LIGHT = "FFF0EE"
AMBER = "A86C24"
AMBER_LIGHT = "FFF4DF"
INK = "18201D"
MUTED = "6C756F"
LINE = "DDE2DC"
PAPER = "F6F7F3"
WHITE = "FFFFFF"

THIN_LINE = Side(style="thin", color=LINE)


def _fill(color: str) -> PatternFill:
    return PatternFill("solid", fgColor=color)


def _merge_value(sheet, cell_range: str, value: Any, **style: Any) -> None:
    sheet.merge_cells(cell_range)
    cell = sheet[cell_range.split(":")[0]]
    cell.value = value
    if "fill" in style:
        cell.fill = _fill(style["fill"])
    if "font" in style:
        cell.font = style["font"]
    if "alignment" in style:
        cell.alignment = style["alignment"]
    if "border" in style:
        cell.border = style["border"]


def _kpi(sheet, start_col: int, end_col: int, label: str, value: Any, detail: str, *, tone: str = NAVY) -> None:
    start = get_column_letter(start_col)
    end = get_column_letter(end_col)
    _merge_value(
        sheet,
        f"{start}5:{end}5",
        label,
        fill=NAVY_LIGHT if tone == NAVY else (GREEN_LIGHT if tone == GREEN else RED_LIGHT),
        font=Font(name="Aptos", size=9, color=MUTED, bold=True),
        alignment=Alignment(vertical="center"),
    )
    _merge_value(
        sheet,
        f"{start}6:{end}7",
        value,
        fill=WHITE,
        font=Font(name="Aptos Display", size=20, color=tone, bold=True),
        alignment=Alignment(horizontal="center", vertical="center"),
    )
    if isinstance(value, (int, float)):
        sheet[f"{start}6"].number_format = "#,##0"
    _merge_value(
        sheet,
        f"{start}8:{end}8",
        detail,
        fill=WHITE,
        font=Font(name="Aptos", size=8, color=MUTED),
        alignment=Alignment(vertical="center"),
    )
    for row in range(5, 9):
        for col in range(start_col, end_col + 1):
            sheet.cell(row, col).border = Border(bottom=THIN_LINE, left=THIN_LINE if col == start_col else None, right=THIN_LINE if col == end_col else None)


def _machine_block(sheet, machine: dict[str, Any], start_row: int, start_col: int, height: int) -> None:
    end_col = start_col + 6
    first = get_column_letter(start_col)
    last = get_column_letter(end_col)
    active = bool(machine.get("active"))
    header_color = NAVY if active else MUTED
    status = "Aktif" if active else "Pasif"

    _merge_value(
        sheet,
        f"{first}{start_row}:{last}{start_row + 1}",
        f"{machine.get('id', '')}  ·  {machine.get('name', '')}     {status}",
        fill=header_color,
        font=Font(name="Aptos Display", size=12, color=WHITE, bold=True),
        alignment=Alignment(vertical="center"),
    )
    headings = ["Sıra", "Ürün", "Çap", "Adet", "Bitiş", "İş emri", "Durum"]
    for offset, heading in enumerate(headings):
        cell = sheet.cell(start_row + 2, start_col + offset, heading)
        cell.fill = _fill(PEACH)
        cell.font = Font(name="Aptos", size=8, color="56301E", bold=True)
        cell.alignment = Alignment(horizontal="center" if offset in {0, 2, 3, 4, 6} else "left", vertical="center")
        cell.border = Border(bottom=THIN_LINE)

    rows = machine.get("rows", [])
    data_height = max(1, height)
    for index in range(data_height):
        row_number = start_row + 3 + index
        item = rows[index] if index < len(rows) else None
        kind = item.get("kind") if item else ""
        background = GREEN_LIGHT if kind == "current" else (WHITE if index % 2 == 0 else PAPER)
        values = (
            [
                "Üretimde" if kind == "current" else item.get("position", ""),
                item.get("product", ""),
                item.get("diameter", ""),
                item.get("quantity", 0),
                item.get("endDate", ""),
                item.get("workOrder", ""),
                "Mevcut iş" if kind == "current" else "Planlı",
            ]
            if item
            else ["—", "Kuyruk boş", "", "", "", "", ""]
        )
        for offset, value in enumerate(values):
            cell = sheet.cell(row_number, start_col + offset, value)
            cell.fill = _fill(background)
            cell.font = Font(name="Aptos", size=8, color=GREEN if kind == "current" and offset == 6 else INK, bold=offset in {1, 6})
            cell.alignment = Alignment(horizontal="center" if offset in {0, 2, 3, 4, 6} else "left", vertical="center")
            cell.border = Border(bottom=THIN_LINE)
            if offset == 3 and isinstance(value, (int, float)):
                cell.number_format = "#,##0"

    footer_row = start_row + 3 + data_height
    _merge_value(
        sheet,
        f"{first}{footer_row}:{last}{footer_row}",
        f"{machine.get('plannedCount', 0)} planlı şarj  ·  {machine.get('plannedQuantity', 0):,.0f} adet",
        fill="FBFCFA",
        font=Font(name="Aptos", size=8, color=MUTED, bold=True),
        alignment=Alignment(horizontal="right", vertical="center"),
    )
    for row in range(start_row, footer_row + 1):
        sheet.cell(row, start_col).border = Border(left=THIN_LINE, bottom=sheet.cell(row, start_col).border.bottom)
        sheet.cell(row, end_col).border = Border(right=THIN_LINE, bottom=sheet.cell(row, end_col).border.bottom)


def _audit_sheet(workbook: Workbook, findings: list[dict[str, Any]]) -> None:
    sheet = workbook.create_sheet("Plan Kontrolü")
    sheet.sheet_view.showGridLines = False
    sheet.freeze_panes = "A4"
    _merge_value(
        sheet,
        "A1:D2",
        "PLAN KONTROLÜ",
        fill=NAVY,
        font=Font(name="Aptos Display", size=17, color=WHITE, bold=True),
        alignment=Alignment(vertical="center"),
    )
    for column, width in {"A": 15, "B": 34, "C": 88, "D": 24}.items():
        sheet.column_dimensions[column].width = width
    headers = ["Seviye", "Kontrol", "Açıklama", "İlgili alan"]
    for index, value in enumerate(headers, 1):
        cell = sheet.cell(4, index, value)
        cell.fill = _fill(PEACH)
        cell.font = Font(name="Aptos", size=9, color="56301E", bold=True)
        cell.border = Border(bottom=THIN_LINE)
    if not findings:
        sheet.append(["Bilgi", "Temel kontroller temiz", "Plan kontrolünde açık bulgu bulunmadı.", ""])
    else:
        for finding in findings:
            sheet.append([
                {"critical": "Kritik", "warning": "Uyarı", "info": "Bilgi"}.get(finding.get("severity"), "Bilgi"),
                finding.get("title", ""),
                finding.get("detail", ""),
                finding.get("target", ""),
            ])
    for row in range(5, sheet.max_row + 1):
        level = sheet.cell(row, 1).value
        tone, background = (RED, RED_LIGHT) if level == "Kritik" else ((AMBER, AMBER_LIGHT) if level == "Uyarı" else (NAVY, NAVY_LIGHT))
        for col in range(1, 5):
            cell = sheet.cell(row, col)
            cell.fill = _fill(background if col == 1 else WHITE)
            cell.font = Font(name="Aptos", size=9, color=tone if col == 1 else INK, bold=col in {1, 2})
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            cell.border = Border(bottom=THIN_LINE)
        sheet.row_dimensions[row].height = 36
    sheet.auto_filter.ref = f"A4:D{sheet.max_row}"


def _shop_floor_header(sheet, label: str, plan: dict[str, Any], generated_at: str, print_range: dict[str, Any], last_column: str) -> None:
    _merge_value(sheet, f"A1:{last_column}2", f"SELSA  ·  {label.upper()} SAHA PLANI", fill=NAVY, font=Font(name="Aptos Display", size=18, color=WHITE, bold=True), alignment=Alignment(vertical="center"))
    scope_label = "Her tezgâh için sıradaki en fazla 10 iş" if print_range.get("mode") == "next-jobs" else f"{print_range.get('startDate', '')} – {print_range.get('endDate', '')}  ·  {print_range.get('dayCount', 0)} gün"
    _merge_value(sheet, "A3:D3", scope_label, fill=WHITE, font=Font(name="Aptos", size=10, color=GREEN, bold=True), alignment=Alignment(vertical="center"))
    _merge_value(sheet, f"E3:{last_column}3", f"Oluşturulma: {generated_at}", fill=WHITE, font=Font(name="Aptos", size=8, color=MUTED), alignment=Alignment(horizontal="right", vertical="center"))
    omitted = int(plan.get("omittedJobCount", 0) or 0)
    note = f"{plan.get('totalJobCount', 0)} iş  ·  {plan.get('totalQuantity', 0):,.0f} adet"
    if omitted:
        note += f"  ·  {omitted} iş yazdırma sınırı dışında"
    _merge_value(sheet, f"A4:{last_column}4", note, fill=AMBER_LIGHT if omitted else NAVY_LIGHT, font=Font(name="Aptos", size=8, color=AMBER if omitted else NAVY, bold=True), alignment=Alignment(vertical="center"))


def _shop_floor_resource_block(sheet, resource: dict[str, Any], start_row: int, start_col: int, row_limit: int, end_col: int) -> None:
    first = get_column_letter(start_col)
    last = get_column_letter(end_col)
    _merge_value(sheet, f"{first}{start_row}:{last}{start_row}", f"{resource.get('id', '')}  ·  {resource.get('name', '')}", fill=NAVY, font=Font(name="Aptos Display", size=10, color=WHITE, bold=True), alignment=Alignment(vertical="center"))
    headings = ["Sıra", "Ürün", "Şarj / iş emri", "Adet", "Başlangıç", "Bitiş", "Durum", "Çap"]
    widths = [7, 17, 19, 10, 12, 12, 11, 8]
    for offset, heading in enumerate(headings):
        cell = sheet.cell(start_row + 1, start_col + offset, heading)
        cell.fill = _fill(PEACH)
        cell.font = Font(name="Aptos", size=7, color="56301E", bold=True)
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = Border(bottom=THIN_LINE)
        sheet.column_dimensions[get_column_letter(start_col + offset)].width = widths[offset]
    rows = list(resource.get("rows", []))[:row_limit]
    for index in range(row_limit):
        item = rows[index] if index < len(rows) else None
        values = [
            "Üretimde" if item and item.get("status") == "current" else (item.get("position", index + 1) if item else ""),
            item.get("product", "") if item else "",
            item.get("workOrder", "") if item else "",
            item.get("quantity", 0) if item else "",
            item.get("startDate", "") if item else "",
            item.get("endDate", "") if item else "",
            ("Mevcut" if item.get("status") == "current" else "Planlı") if item else "",
            (item.get("diameter") or "—") if item else "",
        ]
        background = GREEN_LIGHT if item and item.get("status") == "current" else (WHITE if index % 2 == 0 else PAPER)
        for offset, value in enumerate(values):
            cell = sheet.cell(start_row + 2 + index, start_col + offset, value)
            cell.fill = _fill(background)
            cell.font = Font(name="Aptos", size=7, color=INK, bold=offset in {1, 6})
            cell.alignment = Alignment(horizontal="center" if offset in {0, 3, 4, 5, 6} else "left", vertical="center", shrink_to_fit=True)
            cell.border = Border(bottom=THIN_LINE)
            if offset == 3 and isinstance(value, (int, float)):
                cell.number_format = "#,##0"
    footer_row = start_row + 2 + row_limit
    _merge_value(sheet, f"{first}{footer_row}:{last}{footer_row}", f"{len(rows)} iş  ·  {sum(int(row.get('quantity', 0) or 0) for row in rows):,.0f} adet", fill=NAVY_LIGHT, font=Font(name="Aptos", size=7, color=NAVY, bold=True), alignment=Alignment(horizontal="right", vertical="center"))


def _resource_shop_floor_sheet(workbook: Workbook, plan: dict[str, Any], generated_at: str, print_range: dict[str, Any]) -> None:
    process = str(plan.get("process") or "")
    label = str(plan.get("label") or "Operasyon")
    sheet = workbook.create_sheet(f"{label} Saha Planı"[:31])
    sheet.sheet_view.showGridLines = False
    sheet.page_setup.orientation = "landscape"
    sheet.page_setup.paperSize = sheet.PAPERSIZE_A4
    sheet.page_setup.fitToWidth = 1
    sheet.page_setup.fitToHeight = 0
    sheet.sheet_properties.pageSetUpPr.fitToPage = True
    sheet.print_title_rows = "1:4"
    resources = list(plan.get("resources", []))
    if process == "turning":
        _shop_floor_header(sheet, label, plan, generated_at, print_range, "Q")
        for index, resource in enumerate(resources[:16]):
            page = index // 8
            slot = index % 8
            start_row = 6 + page * 58 + (slot // 2) * 14
            start_col, end_col = (1, 8) if slot % 2 == 0 else (10, 17)
            _shop_floor_resource_block(sheet, resource, start_row, start_col, 10, end_col)
        if len(resources) > 8:
            sheet.row_breaks.append(Break(id=62))
        last_row = 61 if len(resources) <= 8 else 119
        sheet.print_area = f"A1:Q{last_row}"
    sheet.sheet_properties.pageSetUpPr.fitToPage = True


def _long_shop_floor_sheet(workbook: Workbook, plan: dict[str, Any], generated_at: str, print_range: dict[str, Any]) -> None:
    label = str(plan.get("label") or "Operasyon")
    sheet = workbook.create_sheet(f"{label} Saha Planı"[:31])
    sheet.sheet_view.showGridLines = False
    sheet.freeze_panes = "A6"
    sheet.page_setup.orientation = "landscape"
    sheet.page_setup.paperSize = sheet.PAPERSIZE_A4
    sheet.page_setup.fitToWidth = 1
    sheet.page_setup.fitToHeight = 0
    sheet.sheet_properties.pageSetUpPr.fitToPage = True
    sheet.print_title_rows = "1:5"
    sheet.page_margins.left = sheet.page_margins.right = 0.3
    sheet.page_margins.top = sheet.page_margins.bottom = 0.35
    for header_row in range(1, 6):
        sheet.row_dimensions[header_row].height = 18

    last_column = "I" if plan.get("process") == "drilling" else "J"
    _shop_floor_header(sheet, label, plan, generated_at, print_range, last_column)
    headers = ["İstasyon", "İstasyon adı", "Durum", "Sıra", "Ürün", "Şarj / iş emri", "Adet", "Başlangıç", "Bitiş", "Çap"]
    widths = [14, 24, 12, 8, 20, 20, 12, 14, 14, 10]
    if plan.get("process") == "drilling":
        headers, widths = headers[:-1], widths[:-1]
    for column, (heading, width) in enumerate(zip(headers, widths, strict=True), 1):
        cell = sheet.cell(5, column, heading)
        cell.fill = _fill(PEACH)
        cell.font = Font(name="Aptos", size=8, color="56301E", bold=True)
        cell.border = Border(bottom=THIN_LINE)
        sheet.column_dimensions[get_column_letter(column)].width = width
    row_number = 6
    written = 0
    for resource in plan.get("resources", []):
        for item in resource.get("rows", []):
            values = [resource.get("id", ""), resource.get("name", ""), "Üretimde" if item.get("status") == "current" else "Planlı", item.get("position", ""), item.get("product", ""), item.get("workOrder", ""), item.get("quantity", 0), item.get("startDate", ""), item.get("endDate", ""), item.get("diameter") or "—"]
            background = GREEN_LIGHT if item.get("status") == "current" else (WHITE if written % 2 == 0 else PAPER)
            if plan.get("process") == "drilling":
                values = values[:9]
            for column, value in enumerate(values, 1):
                cell = sheet.cell(row_number, column, value)
                cell.fill = _fill(background)
                cell.font = Font(name="Aptos", size=8, color=INK, bold=column in {1, 3, 5})
                cell.alignment = Alignment(horizontal="center" if column in {3, 4, 7, 8, 9, 10} else "left", vertical="center", shrink_to_fit=True)
                cell.border = Border(bottom=THIN_LINE)
                if column == 7:
                    cell.number_format = "#,##0"
            sheet.row_dimensions[row_number].height = 14
            row_number += 1
            written += 1
            if written % 31 == 0:
                sheet.row_breaks.append(Break(id=row_number - 1))
    if sheet.row_breaks.brk and sheet.row_breaks.brk[-1].id == row_number - 1:
        sheet.row_breaks.brk.pop()
    sheet.print_area = f"A1:{last_column}{max(6, row_number - 1)}"


def _shop_floor_plan_sheet(workbook: Workbook, plan: dict[str, Any], generated_at: str, print_range: dict[str, Any]) -> None:
    if plan.get("process") == "turning":
        _resource_shop_floor_sheet(workbook, plan, generated_at, print_range)
    else:
        _long_shop_floor_sheet(workbook, plan, generated_at, print_range)


def _operation_plan_sheet(workbook: Workbook, plan: dict[str, Any], generated_at: str, print_range: dict[str, Any] | None = None) -> None:
    if print_range:
        _shop_floor_plan_sheet(workbook, plan, generated_at, print_range)
        return
    label = str(plan.get("label") or "Operasyon")
    sheet = workbook.create_sheet(f"{label} Planı"[:31])
    sheet.sheet_view.showGridLines = False
    sheet.freeze_panes = "A6"
    sheet.page_setup.orientation = "landscape"
    sheet.page_setup.fitToWidth = 1
    sheet.sheet_properties.pageSetUpPr.fitToPage = True
    sheet.print_title_rows = "1:5"

    last_column = "I" if plan.get("process") == "drilling" else "J"
    _merge_value(
        sheet,
        f"A1:{last_column}2",
        f"SELSA  ·  {label.upper()} GENEL PLANI",
        fill=NAVY,
        font=Font(name="Aptos Display", size=18, color=WHITE, bold=True),
        alignment=Alignment(vertical="center"),
    )
    _merge_value(
        sheet,
        "A3:D3",
        f"{plan.get('totalJobCount', 0)} iş  ·  {plan.get('totalQuantity', 0):,.0f} adet",
        fill=WHITE,
        font=Font(name="Aptos", size=9, color=GREEN, bold=True),
        alignment=Alignment(vertical="center"),
    )
    _merge_value(
        sheet,
        f"E3:{last_column}3",
        f"Oluşturulma: {generated_at}",
        fill=WHITE,
        font=Font(name="Aptos", size=8, color=MUTED),
        alignment=Alignment(horizontal="right", vertical="center"),
    )

    headers = ["İstasyon", "İstasyon adı", "Durum", "Sıra", "Ürün", "Şarj / iş emri", "Adet", "Başlangıç", "Bitiş", "Çap"]
    widths = [14, 25, 14, 9, 21, 20, 14, 16, 16, 10]
    if plan.get("process") == "drilling":
        headers, widths = headers[:-1], widths[:-1]
    for column, (heading, width) in enumerate(zip(headers, widths, strict=True), 1):
        cell = sheet.cell(5, column, heading)
        cell.fill = _fill(PEACH)
        cell.font = Font(name="Aptos", size=8, color="56301E", bold=True)
        cell.alignment = Alignment(horizontal="right" if column == 7 else "left", vertical="center")
        cell.border = Border(bottom=THIN_LINE)
        sheet.column_dimensions[get_column_letter(column)].width = width

    row_number = 6
    for resource in plan.get("resources", []):
        resource_rows = resource.get("rows", [])
        if not resource_rows:
            values = [resource.get("id", ""), resource.get("name", ""), "Planlı iş yok", "", "", "", 0, "", "", ""]
            resource_rows = [None]
        for index, item in enumerate(resource_rows):
            if item is not None:
                values = [
                    resource.get("id", ""), resource.get("name", ""),
                    "Üretimde" if item.get("status") == "current" else "Planlı",
                    item.get("position", index + 1), item.get("product", ""), item.get("workOrder", ""),
                    max(0, int(item.get("quantity", 0))), item.get("startDate", ""), item.get("endDate", ""), item.get("diameter") or "—",
                ]
            background = GREEN_LIGHT if item is not None and item.get("status") == "current" else (WHITE if row_number % 2 == 0 else PAPER)
            if plan.get("process") == "drilling":
                values = values[:9]
            for column, value in enumerate(values, 1):
                cell = sheet.cell(row_number, column, value)
                cell.fill = _fill(background)
                cell.font = Font(name="Aptos", size=8, color=INK, bold=column in {1, 3, 5})
                cell.alignment = Alignment(horizontal="right" if column == 7 else "left", vertical="center")
                cell.border = Border(bottom=THIN_LINE)
                if column == 7:
                    cell.number_format = "#,##0"
            row_number += 1

    last_row = max(6, row_number - 1)
    sheet.auto_filter.ref = f"A5:{last_column}{last_row}"
    sheet.print_area = f"A1:{last_column}{last_row}"


def build_overview_workbook(payload: dict[str, Any]) -> bytes:
    workbook = Workbook()
    selected_process = payload.get("selectedProcess")
    if selected_process:
        empty_sheet = workbook.active
        generated = payload.get("generatedAt") or datetime.now(timezone.utc).isoformat()
        selected_plan = next((plan for plan in payload.get("operationPlans", []) if plan.get("process") == selected_process), None)
        if selected_plan is not None:
            _operation_plan_sheet(workbook, selected_plan, generated, payload.get("printRange"))
        else:
            fallback_labels = {"turning": "Torna", "drilling": "Delme", "deburring": "Çapak Alma", "gkm": "GKM"}
            _operation_plan_sheet(workbook, {"process": selected_process, "label": fallback_labels.get(selected_process, "Operasyon"), "totalQuantity": 0, "totalJobCount": 0, "resources": []}, generated, payload.get("printRange"))
        workbook.remove(empty_sheet)
        output = BytesIO()
        workbook.save(output)
        return output.getvalue()

    sheet = workbook.active
    sheet.title = "Genel Bakış"
    sheet.sheet_view.showGridLines = False
    sheet.freeze_panes = "A10"
    sheet.page_setup.orientation = "landscape"
    sheet.page_setup.fitToWidth = 1
    sheet.sheet_properties.pageSetUpPr.fitToPage = True

    for column in range(1, 16):
        sheet.column_dimensions[get_column_letter(column)].width = 12
    sheet.column_dimensions["B"].width = 18
    sheet.column_dimensions["F"].width = 17
    sheet.column_dimensions["J"].width = 18
    sheet.column_dimensions["N"].width = 17
    sheet.column_dimensions["H"].width = 3

    _merge_value(
        sheet,
        "A1:O2",
        "SELSA  ·  ÜRETİM GENEL BAKIŞ",
        fill=NAVY,
        font=Font(name="Aptos Display", size=18, color=WHITE, bold=True),
        alignment=Alignment(vertical="center"),
    )
    generated = payload.get("generatedAt") or datetime.now(timezone.utc).isoformat()
    state = "Girdiler değişti · plan güncel değil" if payload.get("dirty") else ("Planlandı" if payload.get("planState") == "planned" else "Plan henüz çalıştırılmadı")
    _merge_value(sheet, "A3:H3", state, fill=WHITE, font=Font(name="Aptos", size=9, color=RED if payload.get("dirty") else GREEN, bold=True), alignment=Alignment(vertical="center"))
    _merge_value(sheet, "I3:O3", f"Oluşturulma: {generated}", fill=WHITE, font=Font(name="Aptos", size=8, color=MUTED), alignment=Alignment(horizontal="right", vertical="center"))

    summary = payload.get("summary", {})
    demand = max(0, int(summary.get("demand", 0)))
    planned = max(0, int(summary.get("planned", 0)))
    shortage = max(0, demand - planned)
    coverage = planned / demand if demand else 0
    _kpi(sheet, 1, 3, "SİPARİŞ TALEBİ", demand, "adet", tone=NAVY)
    _kpi(sheet, 4, 6, "KARŞILANAN", planned if payload.get("planState") == "planned" else "—", f"%{coverage * 100:.1f} karşılama" if payload.get("planState") == "planned" else "hesaplanmadı", tone=GREEN)
    _kpi(sheet, 7, 9, "EKSİK ÜRETİM", shortage if payload.get("planState") == "planned" else "—", f"{summary.get('unplannedBatchCount', 0)} planlanamayan şarj" if payload.get("planState") == "planned" else "hesaplanmadı", tone=RED)
    _kpi(sheet, 10, 12, "PLANLI ŞARJ", summary.get("plannedBatchCount", 0) if payload.get("planState") == "planned" else "—", f"{summary.get('plannedMachineCount', 0)} tezgaha dağıtıldı", tone=NAVY)
    _kpi(sheet, 13, 15, "AKTİF TEZGAH", f"{summary.get('activeMachineCount', 0)} / {summary.get('machineCount', 0)}", f"{summary.get('machinesWithWorkCount', 0)} tezgah iş gösteriyor", tone=NAVY)

    machines = payload.get("machines", [])
    current_row = 10
    for index in range(0, len(machines), 2):
        pair = machines[index:index + 2]
        height = max(1, *(len(machine.get("rows", [])) for machine in pair))
        _machine_block(sheet, pair[0], current_row, 1, height)
        if len(pair) > 1:
            _machine_block(sheet, pair[1], current_row, 9, height)
        current_row += height + 6

    sheet.print_area = f"A1:O{max(10, current_row - 2)}"
    sheet.auto_filter.ref = None
    for plan in payload.get("operationPlans", []):
        _operation_plan_sheet(workbook, plan, generated)
    _audit_sheet(workbook, payload.get("findings", []))

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()
