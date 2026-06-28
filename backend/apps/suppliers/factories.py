"""Test factories for suppliers."""

import factory

from .models import Supplier


class SupplierFactory(factory.django.DjangoModelFactory[Supplier]):
    class Meta:
        model = Supplier

    name = factory.Sequence(lambda n: f"Поставщик {n}")
    inn = factory.Sequence(lambda n: f"{7700000000 + n}")
    currency = Supplier.Currency.RUB
