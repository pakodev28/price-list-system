"""Normalization helper tests."""

from apps.catalog.normalization import normalize_article, normalize_name


def test_normalize_article_strips_separators() -> None:
    assert normalize_article("ВВГ-нг(А)-LS") == normalize_article("ВВГ нг А LS")


def test_normalize_name_unifies_decimal_and_spacing() -> None:
    assert normalize_name("Кабель  3,5 мм") == "кабель 3.5 мм"
