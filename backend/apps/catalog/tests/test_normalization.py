"""Normalization helper tests."""

from apps.catalog.normalization import normalize_article, normalize_name


def test_normalize_article_strips_separators() -> None:
    assert normalize_article("ВВГ-нг(А)-LS") == normalize_article("ВВГ нг А LS")


def test_normalize_name_unifies_decimal_and_spacing() -> None:
    assert normalize_name("Кабель  3,5 мм") == "кабель 3.5 мм"


def test_synonyms_collapse_abbreviation_to_canonical() -> None:
    """A noisy abbreviation and the canonical name normalize to the same string."""
    assert normalize_name("Мор. фрахт Шанхай–Владивосток") == normalize_name(
        "Морской фрахт Шанхай–Владивосток"
    )


def test_synonyms_expand_each_abbreviation() -> None:
    assert "железнодорожная" in normalize_name("ЖД Чунцин Москва")
    assert "авиаперевозка" in normalize_name("Авиа Гуанчжоу Москва")
    assert "автодоставка" in normalize_name("Авто Владивосток Москва")
    assert "контейнер" in normalize_name("Хран. конт. на СВХ")


def test_synonyms_do_not_double_expand_full_words() -> None:
    """A canonical word is not re-expanded ("морской" stays "морской")."""
    assert normalize_name("Морской фрахт") == "морской фрахт"
    assert normalize_name("Авиаперевозка Шанхай") == "авиаперевозка шанхай"
