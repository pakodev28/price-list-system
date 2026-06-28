"""Upload validation for Excel imports."""

from pathlib import Path
from typing import Any

from django.core.exceptions import ValidationError

ALLOWED_EXTENSIONS = (".xlsx", ".xls")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def validate_excel_file(file: Any) -> None:
    """Reject non-Excel extensions and oversized uploads with a clear message."""
    extension = Path(file.name).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"Поддерживаются только {', '.join(ALLOWED_EXTENSIONS)}; получено «{extension or '—'}»."
        )
    if file.size and file.size > MAX_FILE_SIZE:
        raise ValidationError(
            f"Файл больше {MAX_FILE_SIZE // (1024 * 1024)} МБ ({file.size} байт)."
        )
