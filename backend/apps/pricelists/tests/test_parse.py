"""Price list parsing task tests (reader monkeypatched — file content unused)."""

from decimal import Decimal

import pytest
from django.core.files.base import ContentFile

from apps.imports.constants import ImportStatus
from apps.pricelists.factories import PriceListFactory
from apps.pricelists.models import PriceListItem
from apps.pricelists.tasks import parse_price_list

pytestmark = pytest.mark.django_db


def test_parse_creates_items_and_skips_blank(
    monkeypatch: pytest.MonkeyPatch, settings: object, tmp_path: object
) -> None:
    settings.MEDIA_ROOT = tmp_path  # type: ignore[attr-defined]
    price_list = PriceListFactory()
    price_list.file.save("prices.xlsx", ContentFile(b"placeholder"), save=True)
    rows = [
        ["A-1", "Кабель", "м", "100,5"],
        ["A-2", "Труба", "шт", "200"],
        ["", "", "", ""],  # blank name -> skipped
    ]
    monkeypatch.setattr("apps.pricelists.tasks.iter_rows", lambda *_a, **_k: iter(rows))

    parse_price_list(price_list.id)
    price_list.refresh_from_db()

    assert price_list.status == ImportStatus.DONE
    assert price_list.progress == 100
    assert price_list.items.count() == 2
    assert price_list.items.get(article="A-1").price == Decimal("100.5")
    assert price_list.row_errors == []


def test_parse_collects_row_errors(
    monkeypatch: pytest.MonkeyPatch, settings: object, tmp_path: object
) -> None:
    from apps.imports.mapping import to_decimal as real_to_decimal

    settings.MEDIA_ROOT = tmp_path  # type: ignore[attr-defined]
    price_list = PriceListFactory()
    price_list.file.save("prices.xlsx", ContentFile(b"placeholder"), save=True)
    rows = [["A-1", "Кабель", "м", "100"], ["A-2", "Труба", "шт", "BAD"]]
    monkeypatch.setattr("apps.pricelists.tasks.iter_rows", lambda *_a, **_k: iter(rows))

    def flaky_to_decimal(value: object) -> object:
        if value == "BAD":
            raise ValueError("плохая цена")
        return real_to_decimal(value)

    monkeypatch.setattr("apps.pricelists.tasks.to_decimal", flaky_to_decimal)

    parse_price_list(price_list.id)
    price_list.refresh_from_db()

    assert price_list.status == ImportStatus.DONE
    assert price_list.items.count() == 1  # the good row
    assert len(price_list.row_errors) == 1
    assert price_list.row_errors[0]["row"] == 2


def test_parse_failure_is_atomic_and_keeps_previous_items(
    monkeypatch: pytest.MonkeyPatch, settings: object, tmp_path: object
) -> None:
    settings.MEDIA_ROOT = tmp_path  # type: ignore[attr-defined]
    price_list = PriceListFactory()
    price_list.file.save("prices.xlsx", ContentFile(b"placeholder"), save=True)
    price_list.items.create(row_number=1, name="старая позиция")

    rows = [["A-1", "Новая", "м", "10"]]
    monkeypatch.setattr("apps.pricelists.tasks.iter_rows", lambda *_a, **_k: iter(rows))

    def boom(*_a: object, **_k: object) -> None:
        raise RuntimeError("сбой записи в БД")

    monkeypatch.setattr(PriceListItem.objects, "bulk_create", boom)

    with pytest.raises(RuntimeError):
        parse_price_list(price_list.id)

    price_list.refresh_from_db()
    assert price_list.status == ImportStatus.FAILED
    # the delete was rolled back together with the failed insert
    assert price_list.items.count() == 1
    assert price_list.items.get().name == "старая позиция"
