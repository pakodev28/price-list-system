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
