"""End-to-end auto-match task test (LLM disabled — fuzzy path)."""

import pytest

from apps.catalog.factories import CatalogProductFactory
from apps.projects.factories import EstimateFactory
from apps.projects.models import EstimateItem
from apps.projects.tasks import auto_match_estimate

pytestmark = pytest.mark.django_db


def test_auto_match_assigns_catalog_and_completes_progress() -> None:
    estimate = EstimateFactory()
    target = CatalogProductFactory(article="K1", name="Кабель ВВГнг 3х2.5")
    CatalogProductFactory(article="T1", name="Труба стальная 20")
    EstimateItem.objects.create(
        estimate=estimate, row_number=1, name="Кабель ВВГ нг 3x2,5 мм2", article=""
    )

    auto_match_estimate(estimate.id)

    estimate.refresh_from_db()
    item = estimate.items.get()
    assert item.catalog_product_id == target.id
    assert item.match_status == EstimateItem.MatchStatus.MATCHED
    assert item.match_source == EstimateItem.MatchSource.AUTO
    assert estimate.match_progress == 100


def test_auto_match_marks_no_match_when_catalog_empty() -> None:
    estimate = EstimateFactory()
    EstimateItem.objects.create(estimate=estimate, row_number=1, name="Нечто", article="")

    auto_match_estimate(estimate.id)

    item = estimate.items.get()
    assert item.match_status == EstimateItem.MatchStatus.NO_MATCH
    assert item.catalog_product_id is None


def test_auto_match_only_selected_items() -> None:
    estimate = EstimateFactory()
    target = CatalogProductFactory(article="F1", name="Морской фрахт Шанхай Владивосток 40HC")
    first = EstimateItem.objects.create(
        estimate=estimate, row_number=1, name="фрахт Шанхай Владивосток 40HC"
    )
    second = EstimateItem.objects.create(
        estimate=estimate, row_number=2, name="фрахт Шанхай Владивосток 40HC"
    )

    auto_match_estimate(estimate.id, item_ids=[first.id])

    first.refresh_from_db()
    second.refresh_from_db()
    assert first.catalog_product_id == target.id
    assert second.match_status == EstimateItem.MatchStatus.UNMATCHED  # untouched
