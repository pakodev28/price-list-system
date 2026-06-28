"""Excel upload validator tests."""

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.imports.validators import validate_excel_file


def test_accepts_xlsx() -> None:
    validate_excel_file(SimpleUploadedFile("prices.xlsx", b"data"))


def test_rejects_non_excel_extension() -> None:
    with pytest.raises(ValidationError):
        validate_excel_file(SimpleUploadedFile("prices.csv", b"data"))


def test_rejects_oversized_file() -> None:
    big = SimpleUploadedFile("big.xlsx", b"x")
    big.size = 50 * 1024 * 1024
    with pytest.raises(ValidationError):
        validate_excel_file(big)
