"""Header-row detection tests (pure data, no file/DB)."""

from apps.imports.excel import detect_header_row


def test_detects_header_after_title_row() -> None:
    data = [
        ["Прайс-лист 2026", "", ""],
        ["Артикул", "Наименование", "Цена"],
        ["A-1", "Кабель", "100"],
    ]
    assert detect_header_row(data) == 1


def test_header_at_first_row() -> None:
    data = [["Артикул", "Наименование"], ["A-1", "Кабель"]]
    assert detect_header_row(data) == 0


def test_falls_back_to_zero_when_empty() -> None:
    assert detect_header_row([]) == 0
