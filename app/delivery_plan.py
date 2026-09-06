from __future__ import annotations

from datetime import date, datetime
from io import BytesIO
from pathlib import Path
from zoneinfo import ZoneInfo

from openpyxl import load_workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Color, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

MAX_PRODUCTS = 200
# One calendar week can have pre-order actuals, post-order actuals and plan.
MAX_WEEK_COLUMNS = 53 * 3 + 1
TEMPLATE_PRODUCT_ROWS = 43
ACTUAL_KINDS = {"actual", "actual-before-order", "actual-after-order"}
COLUMN_KINDS = ACTUAL_KINDS | {"carryover", "plan"}


class DeliveryPlanError(ValueError):
    pass


def _parse_date(value: str, label: str) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as error:
        raise DeliveryPlanError(f"{label} geçerli bir tarih olmalıdır.") from error


def _sum_formula(row_index: int, column_indexes: list[int]) -> str:
    if not column_indexes:
        return "=0"
    cells = [f"{get_column_letter(column)}{row_index}" for column in column_indexes]
    if column_indexes == list(range(column_indexes[0], column_indexes[-1] + 1)):
        return f"=SUM({cells[0]}:{cells[-1]})"
    return f"=SUM({','.join(cells)})"


def _text(cell, value: str):
    cell.value = value
    cell.data_type = "s"


def build_delivery_plan(template_path: Path, payload: dict) -> bytes:
    if not template_path.exists():
        raise DeliveryPlanError("Teslimat planı şablonu bulunamadı.")
    weeks = payload.get("weeks") or []
    rows = payload.get("rows") or []
    if not 1 <= len(weeks) <= MAX_WEEK_COLUMNS:
        raise DeliveryPlanError(f"Teslimat planı 1–{MAX_WEEK_COLUMNS} hafta sütunu içermelidir.")
    if any(week.get("kind") not in COLUMN_KINDS for week in weeks):
        raise DeliveryPlanError("Teslimat planı sütun türü geçersiz.")
    if len(rows) > MAX_PRODUCTS:
        raise DeliveryPlanError(f"Şablon en fazla {MAX_PRODUCTS} ürün destekliyor.")
    start_date = _parse_date(payload.get("startDate", ""), "Başlangıç tarihi")
    end_date = _parse_date(payload.get("endDate", ""), "Bitiş tarihi")
    if end_date < start_date:
        raise DeliveryPlanError("Bitiş tarihi başlangıç tarihinden önce olamaz.")
    start_monday = start_date.toordinal() - start_date.weekday()
    end_monday = end_date.toordinal() - end_date.weekday()
    if (end_monday - start_monday) // 7 + 1 > 53:
        raise DeliveryPlanError("Teslimat planı en fazla 53 takvim haftasını kapsayabilir.")
    order_date = _parse_date(payload["orderDate"], "Sipariş tarihi") if payload.get("orderDate") else None
    if payload.get("demandSource") == "customer-snapshot" and order_date is None:
        raise DeliveryPlanError("Müşteri dosyasının sipariş tarihi zorunludur.")

    # Build dynamic rows/columns using the planning manager's "Doğru" layout.
    workbook = load_workbook(template_path, keep_links=False)
    for old_sheet in list(workbook.worksheets):
        workbook.remove(old_sheet)
    sheet = workbook.create_sheet("Teslimat Planı")
    workbook.defined_names.clear()
    workbook.calculation.fullCalcOnLoad = True
    workbook.calculation.forceFullCalc = True
    workbook.calculation.calcMode = "auto"
    total_row = 7 + max(TEMPLATE_PRODUCT_ROWS, len(rows))
    last_data_row = total_row - 1
    last_column = 11 + len(weeks)
    last_letter = get_column_letter(last_column)
    actual_columns = [12 + i for i, week in enumerate(weeks) if week["kind"] in ACTUAL_KINDS]
    post_order_columns = [12 + i for i, week in enumerate(weeks) if week["kind"] in {"actual", "actual-after-order"}]
    planned_columns = [12 + i for i, week in enumerate(weeks) if week["kind"] == "plan"]
    widths = {"A": 4.6640625, "B": 21.44140625, "C": 13.88671875,
              "D": 12.6640625, "E": 12.6640625, "F": 10.33203125,
              "G": 9.44140625, "H": 2.109375, "I": 12.6640625,
              "J": 14.33203125, "K": 20.44140625}
    for column, width in widths.items():
        sheet.column_dimensions[column].width = width
    for column in range(12, max(13, last_column) + 1):
        kind = weeks[column - 12]["kind"] if column <= last_column else "plan"
        sheet.column_dimensions[get_column_letter(column)].width = 15 if kind == "carryover" else 13.21875 if kind == "actual-before-order" else 14
    font = Font(name="Liberation Sans", size=11, color="000000")
    rule = Side(style="thin", color="000000")
    table_border = Border(left=rule, right=rule, top=rule, bottom=rule)
    header_fill = PatternFill("solid", fgColor=Color(theme=3, tint=0.8999908444471572))
    metadata_fill = PatternFill("solid", fgColor=Color(theme=7, tint=0.7999816888943144))
    value_fill = PatternFill("solid", fgColor=Color(theme=2))
    gray_fill = PatternFill("solid", fgColor=Color(theme=0, tint=-0.1499984740745262))
    for row in sheet.iter_rows(min_row=1, max_row=total_row + 4, min_col=2, max_col=max(13, last_column)):
        for cell in row:
            cell.font = font
            cell.alignment = Alignment(vertical="center")
    sheet.merge_cells("B1:B2")
    sheet.merge_cells("C1:C2")
    sheet["B1"] = "Güncelleme Tarihi"
    sheet["C1"] = datetime.now(ZoneInfo("Europe/Istanbul")).date()
    sheet["C1"].number_format = "dd/mm/yyyy"
    for coordinate in ["B1", "C1"]:
        sheet[coordinate].font = Font(name="Liberation Sans", size=11, bold=True, color="000000")
        sheet[coordinate].fill = gray_fill
        sheet[coordinate].alignment = Alignment(horizontal="center", vertical="center")
    sheet.row_dimensions[1].height = 14.25
    sheet.row_dimensions[2].height = 14.25
    sheet.row_dimensions[3].height = 14.4
    sheet.row_dimensions[4].height = 14.4
    metadata = [("Başlangıç T.:", start_date), ("Bitiş Tarihi", end_date), ("Sipariş Tarihi", order_date), ("Sipariş Doküman Adı", payload.get("sourceFile") or "Manuel sipariş")]
    for row_index, (label, value) in enumerate(metadata, 1):
        sheet.cell(row_index, 11, label)
        sheet.cell(row_index, 11).fill = metadata_fill
        sheet.merge_cells(start_row=row_index, start_column=12, end_row=row_index, end_column=13)
        value_cell = sheet.cell(row_index, 12)
        value_cell.fill = value_fill
        value_cell.alignment = Alignment(horizontal="right", vertical="center", shrinkToFit=True)
        if row_index == 4:
            _text(sheet.cell(4, 12), value)
        else:
            sheet.cell(row_index, 12, value if value is not None else "Belirtilmedi")
            sheet.cell(row_index, 12).number_format = "dd/mm/yyyy"
    headers = {2: "Tip No", 3: "Ürün Grubu", 4: "Sipariş Adeti", 5: "Teslimat Adeti", 6: "Plan Adet", 7: "Fark", 9: "Dönem içi Toplam Teslimat Adeti", 11: "Tip No"}
    headers.update({12 + i: week["label"] for i, week in enumerate(weeks)})
    colors = {"actual-before-order": Color(theme=2, tint=-0.499984740745262), "actual-after-order": "009A44", "actual": "009A44", "carryover": "C15B26", "plan": "000000"}
    sheet.row_dimensions[6].height = 55.2
    for column, label in headers.items():
        cell = sheet.cell(6, column)
        _text(cell, label)
        cell.font = Font(name="Liberation Sans", size=9 if column >= 12 else 11, bold=True, color=colors[weeks[column - 12]["kind"]] if column >= 12 else "000000")
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
        cell.border = table_border
    for row_index in range(7, total_row):
        sheet.row_dimensions[row_index].height = 13.8
        for column in headers:
            sheet.cell(row_index, column).border = table_border
        for column in [4, 5, 6, 7, 9, *range(12, last_column + 1)]:
            sheet.cell(row_index, column).number_format = "#,##0" if column < 12 else "0"
            sheet.cell(row_index, column).alignment = Alignment(horizontal="right", vertical="center")
    for row_index, row in enumerate(rows, 7):
        product = str(row.get("product") or "").strip().upper()
        quantities = row.get("weeklyQuantities") or []
        if not product:
            raise DeliveryPlanError("Boş malzeme kodu dışa aktarılamaz.")
        if len(quantities) != len(weeks):
            raise DeliveryPlanError(f"{product} için haftalık adet sayısı başlıklarla uyuşmuyor.")
        order_quantity = row.get("orderQuantity", 0)
        if any(not isinstance(q, int) or isinstance(q, bool) or q < 0 for q in [order_quantity, *quantities]):
            raise DeliveryPlanError(f"{product} için adetler negatif olmayan tam sayı olmalıdır.")
        _text(sheet.cell(row_index, 2), product)
        _text(sheet.cell(row_index, 3), str(row.get("family") or "").strip().upper())
        sheet.cell(row_index, 4, order_quantity)
        sheet.cell(row_index, 5, _sum_formula(row_index, post_order_columns))
        sheet.cell(row_index, 6, _sum_formula(row_index, planned_columns))
        sheet.cell(row_index, 7, f"=E{row_index}+F{row_index}-D{row_index}")
        sheet.cell(row_index, 9, _sum_formula(row_index, actual_columns))
        _text(sheet.cell(row_index, 11), product)
        for offset, quantity in enumerate(quantities):
            cell = sheet.cell(row_index, 12 + offset, quantity)
            kind = weeks[offset]["kind"]
            if kind in ACTUAL_KINDS or kind == "carryover":
                cell.font = Font(name="Liberation Sans", size=11, bold=kind in ACTUAL_KINDS, color="C15B26" if kind == "carryover" else "009A44")
            if kind == "actual-before-order":
                cell.number_format = "0;-0;;@"
    sheet.cell(total_row, 2, "Genel Toplam")
    for column in [4, 5, 6, 7, 9, *range(12, last_column + 1)]:
        letter = get_column_letter(column)
        sheet.cell(total_row, column, f"=SUM({letter}7:{letter}{last_data_row})")
    for column in [2, 3, 4, 5, 6, 7, 9, *range(12, last_column + 1)]:
        cell = sheet.cell(total_row, column)
        cell.fill = PatternFill("solid", fgColor="FFF200")
        cell.font = Font(name="Liberation Sans", size=11, bold=True, color="000000")
        cell.number_format = "#,##0"
    sheet.row_dimensions[total_row].height = 15
    summaries = [
        ("Planlanan Toplam Teslimat Adeti", f"=F{total_row}+I{total_row}"),
        ("Planlanan Toplam Piston Adeti", f'=SUMIF(C7:C{last_data_row},"PISTON",F7:F{last_data_row})+SUMIF(C7:C{last_data_row},"PISTON",I7:I{last_data_row})'),
        ("Planlanan Toplam Center Pin Adeti", f'=SUMIF(C7:C{last_data_row},"CENTER PIN",F7:F{last_data_row})+SUMIF(C7:C{last_data_row},"CENTER PIN",I7:I{last_data_row})'),
    ]
    for row_index, (label, formula) in enumerate(summaries, total_row + 2):
        sheet.merge_cells(start_row=row_index, start_column=2, end_row=row_index, end_column=5)
        sheet.cell(row_index, 2, label)
        sheet.cell(row_index, 2).fill = gray_fill
        sheet.cell(row_index, 2).font = Font(name="Liberation Sans", size=11, bold=True, color="000000")
        cell = sheet.cell(row_index, 6, formula)
        cell.number_format = "#,##0"
        cell.font = Font(name="Liberation Sans", size=11, bold=True)
        cell.fill = PatternFill("solid", fgColor="FFFF00")
        sheet.row_dimensions[row_index].height = 15
    sheet.conditional_formatting.add(f"G7:G{total_row}", CellIsRule(operator="lessThan", formula=["0"], fill=PatternFill("solid", fgColor="FFC7CE")))
    sheet.conditional_formatting.add(f"G7:G{total_row}", CellIsRule(operator="greaterThan", formula=["0"], fill=PatternFill("solid", fgColor="C6EFCE")))
    sheet.freeze_panes = "B7"
    sheet.auto_filter.ref = f"B6:{last_letter}{last_data_row}"
    sheet.print_area = f"B1:{get_column_letter(max(13, last_column))}{total_row + 4}"
    sheet.print_title_rows = "1:6"
    sheet.sheet_properties.pageSetUpPr.fitToPage = True
    sheet.page_setup.fitToWidth = 1
    sheet.page_setup.fitToHeight = 0
    sheet.page_setup.orientation = "landscape"
    sheet.page_setup.paperSize = sheet.PAPERSIZE_A4
    sheet.sheet_view.showGridLines = True
    sheet.sheet_view.zoomScale = 90
    output = BytesIO()
    workbook.save(output)
    return output.getvalue()
