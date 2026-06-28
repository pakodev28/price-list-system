"""Excel reading via python-calamine — handles both .xlsx and .xls."""

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from python_calamine import CalamineWorkbook

_HEADER_SCAN_ROWS = 15


@dataclass(frozen=True)
class SheetPreview:
    """Preview payload returned before parsing."""

    sheets: list[str]
    sheet: str
    header_row: int
    columns: list[str]
    rows: list[list[str]]


def _open(path: str) -> CalamineWorkbook:
    return CalamineWorkbook.from_path(path)


def _sheet_data(path: str, sheet: str | None) -> tuple[list[str], str, list[list[Any]]]:
    workbook = _open(path)
    names = list(workbook.sheet_names)
    name = sheet or names[0]
    data = workbook.get_sheet_by_name(name).to_python()
    return names, name, data


def _to_str(value: Any) -> str:
    return "" if value is None else str(value)


def _is_empty(cell: Any) -> bool:
    return cell is None or (isinstance(cell, str) and not cell.strip())


def _looks_numeric(value: str) -> bool:
    try:
        float(value.strip().replace(" ", "").replace(",", "."))
        return True
    except ValueError:
        return False


def detect_header_row(data: list[list[Any]]) -> int:
    """Best-effort header detection.

    Returns the first row that has at least two mostly-textual cells and is
    followed by a non-empty data row; falls back to ``0``.
    """
    for index in range(min(_HEADER_SCAN_ROWS, len(data))):
        non_empty = [c for c in data[index] if not _is_empty(c)]
        if len(non_empty) < 2:
            continue
        text_cells = sum(1 for c in non_empty if isinstance(c, str) and not _looks_numeric(c))
        has_following = index + 1 < len(data) and any(not _is_empty(c) for c in data[index + 1])
        if has_following and text_cells >= max(2, len(non_empty) // 2):
            return index
    return 0


def read_preview(
    path: str, sheet: str | None = None, header_row: int | None = None, limit: int = 20
) -> SheetPreview:
    """Return sheet names, the header columns and a sample of body rows.

    When ``header_row`` is ``None`` the header row is auto-detected.
    """
    names, name, data = _sheet_data(path, sheet)
    resolved = detect_header_row(data) if header_row is None else header_row
    header = data[resolved] if resolved < len(data) else []
    body = data[resolved + 1 : resolved + 1 + limit]
    return SheetPreview(
        sheets=names,
        sheet=name,
        header_row=resolved,
        columns=[_to_str(c) for c in header],
        rows=[[_to_str(c) for c in row] for row in body],
    )


def iter_rows(path: str, sheet: str | None, header_row: int = 0) -> Iterator[list[Any]]:
    """Yield typed data rows located after the header row."""
    _names, _name, data = _sheet_data(path, sheet)
    yield from data[header_row + 1 :]
