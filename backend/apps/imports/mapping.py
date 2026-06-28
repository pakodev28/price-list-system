"""Column mapping and cell value coercion."""

from decimal import Decimal, InvalidOperation
from typing import Any


def get_cell(row: list[Any], index: int | None) -> Any:
    """Safely read a cell by column index; out-of-range/None yields ``None``."""
    if index is None or index < 0 or index >= len(row):
        return None
    return row[index]


def to_text(value: Any) -> str:
    """Coerce a cell to a trimmed string (integers without trailing ``.0``)."""
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def to_decimal(value: Any) -> Decimal | None:
    """Coerce a cell to ``Decimal``, tolerating comma decimals and spaces."""
    if value is None or value == "" or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    text = str(value).strip().replace(" ", "").replace(" ", "").replace(",", ".")
    try:
        return Decimal(text)
    except InvalidOperation:
        return None
