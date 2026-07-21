from __future__ import annotations

from copy import copy
from datetime import date, datetime
from io import BytesIO
from pathlib import Path
from zoneinfo import ZoneInfo

from openpyxl import load_workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import PatternFill
from openpyxl.utils import get_column_letter

MAX_PRODUCTS = 200
MAX_WEEKS = 26
TEMPLATE_PRODUCT_ROWS = 43
TEMPLATE_WEEK_COLUMNS = 6


class DeliveryPlanError(ValueError):
    pass


def _parse_date(value: str, label: str) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as error:
        raise DeliveryPlanError(f"{label} geçerli bir tarih olmalıdır.") from error


def build_delivery_plan(template_path: Path, payload: dict) -> bytes:
    if not template_path.exists():
        raise DeliveryPlanError("Teslimat planı şablonu bulunamadı.")

    weeks = payload.get("weeks") or []
    rows = payload.get("rows") or []
    if not 1 <= len(weeks) <= MAX_WEEKS:
        raise DeliveryPlanError(f"Teslimat planı 1–{MAX_WEEKS} hafta içermelidir.")
    if len(rows) > MAX_PRODUCTS:
        raise DeliveryPlanError(f"Şablon en fazla {MAX_PRODUCTS} aktif sipariş destekliyor.")

    start_date = _parse_date(payload.get("startDate", ""), "Başlangıç tarihi")
    end_date = _parse_date(payload.get("endDate", ""), "Bitiş tarihi")
    if end_date < start_date:
        raise DeliveryPlanError("Bitiş tarihi başlangıç tarihinden önce olamaz.")

    workbook = load_workbook(template_path, keep_links=False)
    sheet = workbook["Teslimat Planı"]
    workbook.defined_names.clear()
    sheet.defined_names.clear()
    workbook.calculation.fullCalcOnLoad = True
    workbook.calculation.forceFullCalc = True
    workbook.calculation.calcMode = "auto"

    if "P4:R4" in {str(item) for item in sheet.merged_cells.ranges}:
        sheet.unmerge_cells("P4:R4")
    sheet.delete_cols(14, 13)

    extra_rows = max(0, len(rows) - TEMPLATE_PRODUCT_ROWS)
    if extra_rows:
        sheet.insert_rows(50, amount=extra_rows)
        for row_index in range(50, 50 + extra_rows):
            for column in range(1, 27):
                source = sheet.cell(49, column)
                target = sheet.cell(row_index, column)
                target._style = copy(source._style)
                target.number_format = source.number_format
                target.alignment = copy(source.alignment)
                target.protection = copy(source.protection)
    total_row = 50 + extra_rows
    summary_header_row = 53 + extra_rows
    summary_total_row = 54 + extra_rows

    extra_week_columns = max(0, len(weeks) - TEMPLATE_WEEK_COLUMNS)
    if extra_week_columns:
        sheet.insert_cols(14, amount=extra_week_columns)
        for column in range(14, 14 + extra_week_columns):
            for row_index in range(1, summary_total_row + 1):
                source = sheet.cell(row_index, 13)
                target = sheet.cell(row_index, column)
                target._style = copy(source._style)
                target.number_format = source.number_format
                target.alignment = copy(source.alignment)
                target.protection = copy(source.protection)
            sheet.column_dimensions[get_column_letter(column)].width = sheet.column_dimensions["M"].width
    weekly_end_column = 7 + len(weeks)
    weekly_end_letter = get_column_letter(weekly_end_column)

    sheet["C1"] = datetime.combine(datetime.now(ZoneInfo("Europe/Istanbul")).date(), datetime.min.time())
    sheet["H1"] = datetime.combine(start_date, datetime.min.time())
    sheet["H2"] = datetime.combine(end_date, datetime.min.time())
    sheet["C4"] = str(payload.get("category") or "Üretim")

    for offset in range(TEMPLATE_WEEK_COLUMNS):
        column = 8 + offset
        sheet.cell(6, column).value = weeks[offset]["label"] if offset < len(weeks) else None
    for offset in range(TEMPLATE_WEEK_COLUMNS, len(weeks)):
        sheet.cell(6, 8 + offset).value = weeks[offset]["label"]

    for row_index in range(7, total_row):
        for column in (*range(2, 6), *range(7, weekly_end_column + 1)):
            sheet.cell(row_index, column).value = None

    for row_index, row in enumerate(rows, start=7):
        product = str(row.get("product") or "").strip().upper()
        if not product:
            raise DeliveryPlanError("Boş malzeme kodu dışa aktarılamaz.")
        quantities = row.get("weeklyQuantities") or []
        if len(quantities) != len(weeks):
            raise DeliveryPlanError(f"{product} için haftalık adet sayısı başlıklarla uyuşmuyor.")
        order_quantity = max(0, int(row.get("orderQuantity") or 0))
        sheet.cell(row_index, 2).value = product
        sheet.cell(row_index, 3).value = f"=SUM(H{row_index}:{weekly_end_letter}{row_index})"
        sheet.cell(row_index, 4).value = order_quantity
        sheet.cell(row_index, 5).value = f"=C{row_index}-D{row_index}"
        sheet.cell(row_index, 7).value = product
        for offset in range(len(weeks)):
            sheet.cell(row_index, 8 + offset).value = max(0, int(quantities[offset]))

    sheet.cell(total_row, 2).value = "Toplam"
    sheet.cell(total_row, 3).value = f"=SUM(C7:C{total_row - 1})"
    sheet.cell(total_row, 4).value = f"=SUM(D7:D{total_row - 1})"
    sheet.cell(total_row, 5).value = f"=C{total_row}-D{total_row}"

    sheet.cell(summary_header_row, 3).value = "Sipariş"
    sheet.cell(summary_header_row, 4).value = "Plan"
    sheet.cell(summary_total_row, 2).value = "Toplam Üretim"
    sheet.cell(summary_total_row, 3).value = f"=D{total_row}"
    sheet.cell(summary_total_row, 4).value = f"=C{total_row}"
    for row_index in (summary_total_row + 1, summary_total_row + 2):
        for column in range(2, 6):
            sheet.cell(row_index, column).value = None

    sheet.conditional_formatting._cf_rules.clear()
    sheet.conditional_formatting.add(f"E7:E{total_row}", CellIsRule(operator="lessThan", formula=["0"], fill=PatternFill("solid", fgColor="FFC7CE")))
    sheet.conditional_formatting.add(f"E7:E{total_row}", CellIsRule(operator="greaterThan", formula=["0"], fill=PatternFill("solid", fgColor="C6EFCE")))
    sheet.freeze_panes = "B7"
    sheet.auto_filter.ref = f"B6:{weekly_end_letter}{total_row - 1}"
    sheet.print_area = f"B1:{weekly_end_letter}{summary_total_row}"
    sheet.sheet_properties.pageSetUpPr.fitToPage = True
    sheet.page_setup.fitToWidth = 1
    sheet.page_setup.fitToHeight = 1
    sheet.page_setup.orientation = "landscape"
    sheet.sheet_view.zoomScale = 90

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()
