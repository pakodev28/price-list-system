"""Seed demo data so the matching flow can be tried immediately.

The last estimate row intentionally has no catalog counterpart, to demonstrate
the red "no match" state alongside confident matches.
"""

from typing import Any

from django.core.management.base import BaseCommand

from apps.catalog.models import CatalogProduct, ProductGroup
from apps.projects.models import Estimate, EstimateItem, Project
from apps.suppliers.models import Supplier

_CATALOG = [
    ("ВВГ-3х2.5", "Кабель ВВГ-нг(А)-LS 3x2,5 мм²", "м", "Кабельная продукция"),
    ("ПВС-2х1.5", "Провод ПВС 2х1.5", "м", "Кабельная продукция"),
    ("VGP-20", "Труба стальная ВГП 20", "м", "Трубы"),
    ("AVB-C16", "Автоматический выключатель C16", "шт", "Электрика"),
]
_ESTIMATE_ROWS = [
    ("Кабель ВВГнг 3х2.5", "м", "120"),
    ("Провод ПВС 2x1,5", "м", "80"),
    ("Труба ВГП 20", "м", "50"),
    ("Щит распределительный навесной", "шт", "2"),
]


class Command(BaseCommand):
    help = "Seed demo catalog, supplier and a parsed estimate ready for auto-match."

    def handle(self, *args: Any, **options: Any) -> None:
        for article, name, unit, group_name in _CATALOG:
            group, _ = ProductGroup.objects.get_or_create(name=group_name)
            CatalogProduct.objects.get_or_create(
                article=article, defaults={"name": name, "unit": unit, "group": group}
            )

        Supplier.objects.get_or_create(
            inn="7701234567", defaults={"name": "ООО «Ромашка»", "currency": "RUB"}
        )

        project, _ = Project.objects.get_or_create(name="Демо-проект")
        estimate, created = Estimate.objects.get_or_create(
            project=project,
            source_filename="demo.xlsx",
            defaults={"status": "done", "progress": 100, "total_rows": len(_ESTIMATE_ROWS)},
        )
        if created:
            for index, (name, unit, quantity) in enumerate(_ESTIMATE_ROWS, start=1):
                EstimateItem.objects.create(
                    estimate=estimate, row_number=index, name=name, unit=unit, quantity=quantity
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Готово. Откройте смету #{estimate.id} во фронтенде и нажмите «ИИ-сопоставление»."
            )
        )
