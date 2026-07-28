from __future__ import annotations

import re
import zipfile
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from io import BytesIO
from pathlib import PurePosixPath
from xml.etree import ElementTree as ET


MAX_XLSX_BYTES = 5 * 1024 * 1024
MAX_UNCOMPRESSED_BYTES = 20 * 1024 * 1024
MAX_ROWS = 1_000
MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


class OrderImportError(ValueError):
    pass


def _normalize_header(value: str) -> str:
    return " ".join(value.strip().lower().replace("ı", "i").replace("ş", "s").split())


def _sheet_paths(archive: zipfile.ZipFile) -> list[tuple[str, str]]:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    relationship_targets = {
        item.attrib["Id"]: item.attrib["Target"]
        for item in relationships.findall(f"{{{PACKAGE_REL_NS}}}Relationship")
    }
    sheets = workbook.findall(f"{{{MAIN_NS}}}sheets/{{{MAIN_NS}}}sheet")
    if not sheets:
        raise OrderImportError("Excel dosyasında okunabilir bir sayfa bulunamadı.")
    paths: list[tuple[str, str]] = []
    for sheet in sheets:
        relationship_id = sheet.attrib.get(f"{{{REL_NS}}}id", "")
        target = relationship_targets.get(relationship_id, "")
        if not target:
            continue
        path = target.lstrip("/") if target.startswith("/") else str(PurePosixPath("xl") / target)
        paths.append((sheet.attrib.get("name", ""), path))
    if not paths:
        raise OrderImportError("Excel dosyasındaki sayfalar açılamadı.")
    return paths


def _first_sheet_path(archive: zipfile.ZipFile) -> str:
    return _sheet_paths(archive)[0][1]


def _sheet_path_by_name(archive: zipfile.ZipFile, expected_name: str) -> str | None:
    expected = expected_name.strip().casefold()
    return next((path for name, path in _sheet_paths(archive) if name.strip().casefold() == expected), None)


def _shared_strings(archive: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    return ["".join(node.text or "" for node in item.iter(f"{{{MAIN_NS}}}t")) for item in root.findall(f"{{{MAIN_NS}}}si")]


def _cell_text(cell: ET.Element, shared: list[str]) -> tuple[str, bool]:
    cell_type = cell.attrib.get("t", "")
    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell.iter(f"{{{MAIN_NS}}}t")), False
    value = cell.findtext(f"{{{MAIN_NS}}}v", default="")
    if cell_type == "s":
        try:
            return shared[int(value)], False
        except (ValueError, IndexError):
            raise OrderImportError("Excel metin tablosu okunamadı.") from None
    return value, cell_type not in {"str", "inlineStr", "s"}


def _parse_integer(value: str, numeric_cell: bool, row_number: int, label: str, allow_negative: bool = False) -> int:
    cleaned = value.strip().replace(" ", "")
    if not cleaned:
        return 0
    if not numeric_cell and re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", cleaned):
        cleaned = cleaned.replace(".", "").replace(",", "")
    elif not numeric_cell:
        cleaned = cleaned.replace(",", ".")
    try:
        number = Decimal(cleaned)
    except InvalidOperation:
        raise OrderImportError(f"{row_number}. satırdaki {label} sayı değil: {value}") from None
    if number < 0 and not allow_negative:
        raise OrderImportError(f"{row_number}. satırdaki {label} negatif olamaz.")
    if number != number.to_integral_value():
        raise OrderImportError(f"{row_number}. satırdaki {label} tam sayı olmalıdır.")
    return int(number)


def _parse_quantity(value: str, numeric_cell: bool, row_number: int) -> int:
    return _parse_integer(value, numeric_cell, row_number, "sipariş adeti")


def _sheet_values(sheet: ET.Element, shared: list[str]) -> dict[int, dict[str, tuple[str, bool]]]:
    values_by_row: dict[int, dict[str, tuple[str, bool]]] = {}
    for cell in sheet.iter(f"{{{MAIN_NS}}}c"):
        reference = cell.attrib.get("r", "")
        match = re.fullmatch(r"([A-Z]+)(\d+)", reference)
        if not match:
            continue
        row_number = int(match.group(2))
        values_by_row.setdefault(row_number, {})[match.group(1)] = _cell_text(cell, shared)
    return values_by_row


def _column_number(column: str) -> int:
    result = 0
    for character in column:
        result = result * 26 + ord(character) - 64
    return result


def _parse_snapshot_date(value: str) -> str:
    cleaned = value.strip()
    for pattern in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(cleaned, pattern).date().isoformat()
        except ValueError:
            continue
    raise OrderImportError(f"Overview tarih değeri okunamadı: {value}")


def _parse_confirmed_overview(values_by_row: dict[int, dict[str, tuple[str, bool]]]) -> dict:
    headers = {column: value.strip() for column, (value, _) in values_by_row.get(1, {}).items()}
    normalized_headers = {_normalize_header(value): column for column, value in headers.items()}
    required = {
        "date": "Date",
        "material": "Material",
        "family of parts": "Family of Parts",
        "unit": "Unit",
        "available quantity": "Available quantity",
        "filter": "Filter",
    }
    missing = [display for normalized, display in required.items() if normalized not in normalized_headers]
    if missing:
        raise OrderImportError(f"'3. Overview (confirmed)' sayfasında beklenen kolonlar eksik: {', '.join(missing)}")

    baseline_columns = [
        (column, value)
        for column, value in headers.items()
        if re.fullmatch(r"<\s*CW\s+\d{1,2}\.\d{4}", value, re.IGNORECASE)
    ]
    if len(baseline_columns) != 1:
        raise OrderImportError("'3. Overview (confirmed)' sayfasında tek bir '< CW nn.yyyy' başlangıç kolonu bulunmalıdır.")
    baseline_column, baseline_label = baseline_columns[0]
    baseline_match = re.fullmatch(r"<\s*CW\s+(\d{1,2})\.(\d{4})", baseline_label, re.IGNORECASE)
    assert baseline_match is not None
    first_week_number = int(baseline_match.group(1))
    first_week_year = int(baseline_match.group(2))

    week_columns: list[dict[str, int | str]] = []
    for column, value in headers.items():
        match = re.fullmatch(r"CW\s+(\d{1,2})\.(\d{4})", value, re.IGNORECASE)
        if not match:
            continue
        iso_week = int(match.group(1))
        iso_year = int(match.group(2))
        try:
            week_start = date.fromisocalendar(iso_year, iso_week, 1)
            week_end = date.fromisocalendar(iso_year, iso_week, 7)
        except ValueError:
            raise OrderImportError(f"Geçersiz ISO hafta başlığı: {value}") from None
        week_columns.append({
            "column": column,
            "columnNumber": _column_number(column),
            "isoYear": iso_year,
            "isoWeek": iso_week,
            "id": f"{iso_year}-W{iso_week:02d}",
            "label": f"CW {iso_week}.{iso_year}",
            "weekStart": week_start.isoformat(),
            "weekEnd": week_end.isoformat(),
        })
    week_columns.sort(key=lambda item: int(item["columnNumber"]))
    if not week_columns:
        raise OrderImportError("'3. Overview (confirmed)' sayfasında 'CW nn.yyyy' haftaları bulunamadı.")
    if (week_columns[0]["isoWeek"], week_columns[0]["isoYear"]) != (first_week_number, first_week_year):
        raise OrderImportError("'< CW' başlangıç kolonu ile ilk haftalık kolon birbiriyle eşleşmiyor.")
    if int(week_columns[0]["columnNumber"]) != _column_number(baseline_column) + 1:
        raise OrderImportError("İlk haftalık kolon '< CW' başlangıç kolonunun hemen sağında olmalıdır.")
    for previous, current in zip(week_columns, week_columns[1:]):
        if date.fromisoformat(str(current["weekStart"])) != date.fromisoformat(str(previous["weekStart"])) + timedelta(days=7):
            raise OrderImportError(f"ISO hafta kolonları kesintisiz olmalıdır: {previous['label']} → {current['label']}")

    date_column = normalized_headers["date"]
    material_column = normalized_headers["material"]
    family_column = normalized_headers["family of parts"]
    unit_column = normalized_headers["unit"]
    available_column = normalized_headers["available quantity"]
    filter_column = normalized_headers["filter"]
    baseline_due_date = (date.fromisoformat(str(week_columns[0]["weekStart"])) - timedelta(days=1)).isoformat()
    products: list[dict] = []
    rows: list[dict[str, int | str]] = []
    seen: dict[str, int] = {}
    snapshot_dates: set[str] = set()
    ignored_blank_rows = 0

    for row_number in sorted(number for number in values_by_row if number > 1):
        cells = values_by_row[row_number]
        product = cells.get(material_column, ("", False))[0].strip().upper()
        if not product:
            if all(not cells.get(column, ("", False))[0].strip() for column in (family_column, available_column, baseline_column)):
                ignored_blank_rows += 1
                continue
            raise OrderImportError(f"{row_number}. satırda Material değeri boş.")
        if len(products) >= MAX_ROWS:
            raise OrderImportError(f"Excel dosyası en fazla {MAX_ROWS} ürün satırı içerebilir.")
        if not re.fullmatch(r"[A-Z0-9][A-Z0-9._/-]{1,63}", product):
            raise OrderImportError(f"{row_number}. satırdaki Material değeri geçersiz: {product}")
        if product in seen:
            raise OrderImportError(f"{product} tipi {seen[product]} ve {row_number}. satırlarda tekrar ediyor.")
        if cells.get(filter_column, ("", False))[0].strip().casefold() != "balance (confirmed)":
            raise OrderImportError(f"{row_number}. satır 'Balance (confirmed)' kaydı değil.")

        snapshot_dates.add(_parse_snapshot_date(cells.get(date_column, ("", False))[0]))
        available_text, available_numeric = cells.get(available_column, ("", True))
        baseline_text, baseline_numeric = cells.get(baseline_column, ("", True))
        if not available_text.strip() or not baseline_text.strip():
            raise OrderImportError(f"{row_number}. satırda stok veya '< CW' bakiyesi boş; Excel formülleri hesaplanmış olmalıdır.")
        available_quantity = _parse_integer(available_text, available_numeric, row_number, "Available quantity")
        baseline_balance = _parse_integer(baseline_text, baseline_numeric, row_number, "'< CW' bakiyesi", allow_negative=True)
        prior_demand = max(0, -baseline_balance)

        cumulative_quantity = prior_demand
        weekly_demands: list[dict] = []
        for week in week_columns:
            week_text, week_numeric = cells.get(str(week["column"]), ("", True))
            if not week_text.strip():
                raise OrderImportError(f"{row_number}. satırdaki {week['label']} bakiyesi boş; Excel formülleri hesaplanmış olmalıdır.")
            balance = _parse_integer(week_text, week_numeric, row_number, f"{week['label']} bakiyesi", allow_negative=True)
            required_quantity = max(0, -balance)
            next_cumulative_quantity = max(cumulative_quantity, required_quantity)
            quantity = next_cumulative_quantity - cumulative_quantity
            cumulative_quantity = next_cumulative_quantity
            weekly_demands.append({
                "weekId": week["id"],
                "isoYear": week["isoYear"],
                "isoWeek": week["isoWeek"],
                "label": week["label"],
                "weekStart": week["weekStart"],
                "weekEnd": week["weekEnd"],
                "quantity": quantity,
                "cumulativeQuantity": cumulative_quantity,
                "requiredQuantity": required_quantity,
                "balance": balance,
            })

        family = cells.get(family_column, ("", False))[0].strip()
        unit = cells.get(unit_column, ("", False))[0].strip()
        products.append({
            "product": product,
            "family": family,
            "unit": unit,
            "availableQuantity": available_quantity,
            "baselineBalance": baseline_balance,
            "priorDemand": prior_demand,
            "baselineDueDate": baseline_due_date,
            "weeklyDemands": weekly_demands,
            "totalDemand": cumulative_quantity,
        })
        rows.append({"product": product, "quantity": cumulative_quantity})
        seen[product] = row_number

    if not products:
        raise OrderImportError("'3. Overview (confirmed)' sayfasında ürün satırı bulunamadı.")
    if len(snapshot_dates) != 1:
        raise OrderImportError("'3. Overview (confirmed)' satırlarında tek bir ortak Date değeri bulunmalıdır.")

    weeks = []
    for week in week_columns:
        quantity = sum(
            int(next(item["quantity"] for item in product["weeklyDemands"] if item["weekId"] == week["id"]))
            for product in products
        )
        weeks.append({key: value for key, value in week.items() if key not in {"column", "columnNumber"}} | {"quantity": quantity})
    active = [product for product in products if int(product["totalDemand"]) > 0]
    first_week_requirement = sum(int(product["weeklyDemands"][0]["cumulativeQuantity"]) for product in products)
    last_week_requirement = sum(int(product["totalDemand"]) for product in products)
    return {
        "format": "confirmed-overview",
        "calculationModel": "net-shortage-v1",
        "sheetName": "3. Overview (confirmed)",
        "snapshotDate": next(iter(snapshot_dates)),
        "baselineLabel": baseline_label,
        "baselineDueDate": baseline_due_date,
        "weeks": weeks,
        "products": products,
        "rows": rows,
        "summary": {
            "productCount": len(products),
            "orderCount": len(active),
            "totalQuantity": last_week_requirement,
            "openingStock": sum(int(product["availableQuantity"]) for product in products),
            "priorDemand": sum(int(product["priorDemand"]) for product in products),
            "firstWeekRequirement": first_week_requirement,
            "lastWeekRequirement": last_week_requirement,
            "weekCount": len(weeks),
            "firstWeek": weeks[0]["id"],
            "lastWeek": weeks[-1]["id"],
            "ignoredBlankRows": ignored_blank_rows,
        },
    }


def _parse_simple_order_sheet(values_by_row: dict[int, dict[str, tuple[str, bool]]]) -> dict:
    values_by_row = {
        row_number: {column: value for column, value in cells.items() if column in {"A", "B"}}
        for row_number, cells in values_by_row.items()
    }

    first_header = _normalize_header(values_by_row.get(1, {}).get("A", ("", False))[0])
    second_header = _normalize_header(values_by_row.get(1, {}).get("B", ("", False))[0])
    if first_header != "tip no" or second_header not in {"plan adet", "siparis adeti", "siparis adedi"}:
        raise OrderImportError("Beklenen kolonlar bulunamadı. A1 'Tip no', B1 'Sipariş Adeti' veya 'Plan Adet' olmalıdır.")

    rows: list[dict[str, int | str]] = []
    seen: dict[str, int] = {}
    ignored_blank_rows = 0
    for row_number in sorted(number for number in values_by_row if number > 1):
        if len(rows) >= MAX_ROWS:
            raise OrderImportError(f"Excel dosyası en fazla {MAX_ROWS} ürün satırı içerebilir.")
        product = values_by_row[row_number].get("A", ("", False))[0].strip().upper()
        quantity_text, numeric_cell = values_by_row[row_number].get("B", ("", True))
        if not product and not quantity_text.strip():
            ignored_blank_rows += 1
            continue
        if not product:
            raise OrderImportError(f"{row_number}. satırda tip numarası boş.")
        if not re.fullmatch(r"[A-Z0-9][A-Z0-9._/-]{1,63}", product):
            raise OrderImportError(f"{row_number}. satırdaki tip numarası geçersiz: {product}")
        if product in seen:
            raise OrderImportError(f"{product} tipi {seen[product]} ve {row_number}. satırlarda tekrar ediyor.")
        quantity = _parse_quantity(quantity_text, numeric_cell, row_number)
        seen[product] = row_number
        rows.append({"product": product, "quantity": quantity})

    if not rows:
        raise OrderImportError("Excel dosyasında ürün satırı bulunamadı.")
    active = [row for row in rows if row["quantity"] > 0]
    return {
        "format": "simple-orders",
        "rows": rows,
        "summary": {
            "productCount": len(rows),
            "orderCount": len(active),
            "totalQuantity": sum(int(row["quantity"]) for row in active),
            "ignoredBlankRows": ignored_blank_rows,
        },
    }


def parse_order_xlsx(content: bytes) -> dict:
    if not content:
        raise OrderImportError("Excel dosyası boş.")
    if len(content) > MAX_XLSX_BYTES:
        raise OrderImportError("Excel dosyası 5 MB sınırını aşıyor.")
    try:
        with zipfile.ZipFile(BytesIO(content)) as archive:
            if len(archive.infolist()) > 200 or sum(item.file_size for item in archive.infolist()) > MAX_UNCOMPRESSED_BYTES:
                raise OrderImportError("Excel dosyası güvenli boyut sınırlarını aşıyor.")
            shared = _shared_strings(archive)
            confirmed_path = _sheet_path_by_name(archive, "3. Overview (confirmed)")
            target_path = confirmed_path or _first_sheet_path(archive)
            values_by_row = _sheet_values(ET.fromstring(archive.read(target_path)), shared)
    except OrderImportError:
        raise
    except (zipfile.BadZipFile, KeyError, ET.ParseError):
        raise OrderImportError("Dosya geçerli bir .xlsx çalışma kitabı değil.") from None

    return _parse_confirmed_overview(values_by_row) if confirmed_path else _parse_simple_order_sheet(values_by_row)
