"""Matching service tests (LLM disabled — deterministic paths)."""

import pytest

from apps.catalog.factories import CatalogProductFactory
from apps.catalog.models import CatalogProduct
from apps.matching.service import MatchingService
from apps.matching.shortlist import to_candidates

pytestmark = pytest.mark.django_db


def _candidates() -> list:
    return to_candidates(CatalogProduct.objects.all())


def test_exact_article_wins() -> None:
    target = CatalogProductFactory(article="ВВГ-3х2.5", name="Кабель ВВГ 3х2.5")
    CatalogProductFactory(article="ПВС-2х1.5", name="Провод ПВС 2х1.5")

    outcome = MatchingService(use_llm=False).match(
        name="неважно", article="ВВГ 3х2,5", candidates=_candidates()
    )

    assert outcome.source == "article"
    assert outcome.product_id == target.id
    assert outcome.confidence == 1.0


def test_fuzzy_picks_closest_name() -> None:
    target = CatalogProductFactory(article="A1", name="Кабель ВВГнг 3х2.5")
    CatalogProductFactory(article="A2", name="Труба стальная 20")

    outcome = MatchingService(use_llm=False).match(
        name="Кабель ВВГ нг 3x2,5 мм2", article="", candidates=_candidates()
    )

    assert outcome.source == "fuzzy"
    assert outcome.product_id == target.id
    assert outcome.confidence > 0.5


def test_no_candidates_yields_none() -> None:
    outcome = MatchingService(use_llm=False).match(name="Кабель", article="", candidates=[])
    assert outcome.product_id is None
    assert outcome.source == "none"


def test_high_score_accepted_without_llm() -> None:
    target = CatalogProductFactory(article="X1", name="Морской фрахт 40HC")
    outcome = MatchingService(use_llm=False).match(
        name="Морской фрахт 40HC", article="", candidates=_candidates()
    )
    assert outcome.source == "retrieval"
    assert outcome.product_id == target.id
    assert outcome.confidence >= 0.78


def test_weak_match_returns_no_match() -> None:
    CatalogProductFactory(article="X2", name="Морской фрахт Шанхай Владивосток 40HC")
    outcome = MatchingService(use_llm=False).match(
        name="zzzzz qqqqq wwwww", article="", candidates=_candidates()
    )
    assert outcome.product_id is None
    assert outcome.source == "none"


def test_gray_zone_below_floor_is_no_match(settings) -> None:
    """A weak gray-zone score (here ~0.43) must not be asserted as a tentative match.

    Without the LLM it falls through to "no match" instead of linking an unrelated
    catalog product.
    """
    settings.MATCH_FLOOR = 0.50
    CatalogProductFactory(article="P1", name="Провод ПВС 2х1.5")
    outcome = MatchingService(use_llm=False).match(
        name="Гипсокартон влагостойкий 12.5мм", article="", candidates=_candidates()
    )
    assert outcome.product_id is None
    assert outcome.source == "none"
