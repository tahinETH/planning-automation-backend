from __future__ import annotations

import re
import zipfile
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


def _first_sheet_path(archive: zipfile.ZipFile) -> str:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    relationship_targets = {
        item.attrib["Id"]: item.attrib["Target"]
        for item in relationships.findall(f"{{{PACKAGE_REL_NS}}}Relationship")
    }
    first_sheet = workbook.find(f"{{{MAIN_NS}}}sheets/{{{MAIN_NS}}}sheet")
    if first_sheet is None:
        raise OrderImportError("Excel dosyasında okunabilir bir sayfa bulunamadı.")
    relationship_id = first_sheet.attrib.get(f"{{{REL_NS}}}id", "")
    target = relationship_targets.get(relationship_id, "")
    if not target:
        raise OrderImportError("Excel dosyasının ilk sayfası açılamadı.")
    if target.startswith("/"):
        return target.lstrip("/")
    return str(PurePosixPath("xl") / target)


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


def _parse_quantity(value: str, numeric_cell: bool, row_number: int) -> int:
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
        raise OrderImportError(f"{row_number}. satırdaki sipariş adeti sayı değil: {value}") from None
    if number < 0:
        raise OrderImportError(f"{row_number}. satırdaki sipariş adeti negatif olamaz.")
    if number != number.to_integral_value():
        raise OrderImportError(f"{row_number}. satırdaki sipariş adeti tam sayı olmalıdır.")
    return int(number)


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
            sheet = ET.fromstring(archive.read(_first_sheet_path(archive)))
    except OrderImportError:
        raise
    except (zipfile.BadZipFile, KeyError, ET.ParseError):
        raise OrderImportError("Dosya geçerli bir .xlsx çalışma kitabı değil.") from None

    values_by_row: dict[int, dict[str, tuple[str, bool]]] = {}
    for cell in sheet.iter(f"{{{MAIN_NS}}}c"):
        reference = cell.attrib.get("r", "")
        match = re.fullmatch(r"([A-Z]+)(\d+)", reference)
        if not match or match.group(1) not in {"A", "B"}:
            continue
        row_number = int(match.group(2))
        values_by_row.setdefault(row_number, {})[match.group(1)] = _cell_text(cell, shared)

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
        "rows": rows,
        "summary": {
            "productCount": len(rows),
            "orderCount": len(active),
            "totalQuantity": sum(int(row["quantity"]) for row in active),
            "ignoredBlankRows": ignored_blank_rows,
        },
    }
