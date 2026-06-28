"""Test factories for price lists."""

import factory

from apps.suppliers.factories import SupplierFactory

from .models import PriceList


class PriceListFactory(factory.django.DjangoModelFactory[PriceList]):
    class Meta:
        model = PriceList

    supplier = factory.SubFactory(SupplierFactory)
    source_filename = "prices.xlsx"
    mapping = {"article": 0, "name": 1, "unit": 2, "price": 3}
