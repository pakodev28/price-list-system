"""seed_large management command smoke test (tiny counts for speed)."""

import pytest
from django.core.management import call_command

from apps.catalog.models import CatalogProduct
from apps.pricelists.models import PriceListItem
from apps.projects.models import EstimateItem
from apps.suppliers.models import Supplier

pytestmark = pytest.mark.django_db


def test_seed_large_creates_expected_volume() -> None:
    call_command(
        "seed_large",
        catalog=20,
        suppliers=2,
        pricelist_items=5,
        projects=1,
        estimates_per_project=1,
        estimate_items=8,
        seed=1,
    )

    assert CatalogProduct.objects.count() == 20
    assert Supplier.objects.count() == 2
    assert PriceListItem.objects.count() == 2 * 5
    assert EstimateItem.objects.count() == 1 * 1 * 8
    # noisy variants must still resolve to real catalog names for matching
    assert EstimateItem.objects.exclude(name="").count() == 8


def test_seed_large_exceeds_pool_with_unique_articles() -> None:
    """Requesting more products than the canonical pool still yields unique articles."""
    count = 1500  # above the canonical pool, so generation must cycle with variants
    call_command(
        "seed_large",
        catalog=count,
        suppliers=1,
        pricelist_items=1,
        projects=1,
        estimates_per_project=1,
        estimate_items=1,
        seed=2,
    )

    assert CatalogProduct.objects.count() == count
    assert CatalogProduct.objects.values("article").distinct().count() == count
