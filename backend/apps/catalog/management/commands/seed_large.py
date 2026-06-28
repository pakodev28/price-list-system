"""Generate a large, realistic dataset for manual and load testing.

Usage (inside the backend container):
    python manage.py seed_large                       # ~1200 products, 30 suppliers, …
    python manage.py seed_large --catalog 3000 --suppliers 60
    python manage.py seed_large --clear               # wipe existing data first

Estimate / price-list items use *noisy* variants of catalog names (abbreviations,
swapped separators, reordered words) plus ~10% unrelated rows, so matching has
realistic work to do.
"""

import random
import uuid
from decimal import Decimal
from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import CatalogProduct, ProductGroup
from apps.pricelists.models import PriceList, PriceListItem
from apps.projects.models import Estimate, EstimateItem, Project
from apps.suppliers.models import Supplier

_BRANDS = ["IEK", "ABB", "Schneider", "Legrand", "DKC"]
_COMPANY_STEMS = [
    "СтройМонтаж",
    "ЭлектроКомплект",
    "ТехноКабель",
    "ЭнергоСбыт",
    "ПромСнаб",
    "ГлавЭлектро",
    "СибКабель",
    "УралМонтаж",
    "МегаВатт",
    "СтройРесурс",
    "Вольтаж",
]
_OBJECTS = [
    "ЖК «Северный»",
    "БЦ «Восход»",
    "Школа №12",
    "Склад логистики",
    "ТЦ «Радуга»",
    "Завод №3",
    "Поликлиника №7",
    "Детсад «Солнышко»",
]
_JUNK = [
    "Услуги монтажа",
    "Доставка материалов",
    "Накладные расходы",
    "Пусконаладочные работы",
    "Демонтаж старой проводки",
    "Прочие материалы",
]


def _catalog_pool() -> list[tuple[str, str, str]]:
    """Canonical ``(name, unit, group)`` catalog entries (construction materials)."""
    pool: list[tuple[str, str, str]] = []
    cables = "Кабельная продукция"
    for kind in ["ВВГ", "ВВГнг(А)-LS", "NYM", "КГ", "ВБбШв", "АВВГ", "ПвБбШп", "КВВГ"]:
        for cores in (1, 2, 3, 4, 5):
            for sec in ("0.75", "1.5", "2.5", "4", "6", "10", "16", "25", "35", "50"):
                pool.append((f"Кабель {kind} {cores}х{sec}", "м", cables))
    for kind in ["ПВС", "ШВВП", "ПУГНП", "ПВ-3"]:
        for cores in (2, 3, 4, 5):
            for sec in ("0.5", "0.75", "1.5", "2.5", "4", "6"):
                pool.append((f"Провод {kind} {cores}х{sec}", "м", cables))
    pipes = "Трубы и фитинги"
    for mat in [
        "стальная ВГП",
        "полипропиленовая PN20",
        "ПНД ПЭ100",
        "медная",
        "гофрированная ПВХ",
        "металлопластиковая",
    ]:
        for diam in (16, 20, 25, 32, 40, 50, 63, 90, 110):
            for series in ("", " SDR11", " PN10", " усиленная"):
                pool.append((f"Труба {mat} Ø{diam}{series}", "м", pipes))
    electrical = "Электрооборудование"
    for curve in ("B", "C", "D"):
        for rating in (6, 10, 16, 20, 25, 32, 40, 50, 63):
            for poles in ("1P", "2P", "3P"):
                for brand in _BRANDS:
                    pool.append(
                        (
                            f"Автоматический выключатель {brand} {curve}{rating} {poles}",
                            "шт",
                            electrical,
                        )
                    )
    devices = "Розетки и выключатели"
    for kind in [
        "Розетка о/у",
        "Розетка с/у с з/к",
        "Выключатель 1-кл",
        "Выключатель 2-кл",
        "Розетка двойная",
        "Рамка 1-постовая",
    ]:
        for brand in _BRANDS:
            for color in ("белый", "крем", "антрацит"):
                pool.append((f"{kind} {brand} ({color})", "шт", devices))
    light = "Освещение"
    for kind in [
        "Светильник LED панель",
        "Светильник LED линейный",
        "Светильник ДПО",
        "Светильник ДВО",
        "Прожектор LED",
        "Светильник аварийный",
    ]:
        for power in (12, 18, 24, 36, 40, 48, 60, 100):
            pool.append((f"{kind} {power}Вт", "шт", light))
    trays = "Кабеленесущие системы"
    for width in (16, 25, 40, 60, 80, 100):
        for height in (10, 16, 25, 40, 60):
            pool.append((f"Кабель-канал {width}х{height}", "м", trays))
    for kind in ["Лоток лестничный", "Лоток перфорированный", "Короб металлический"]:
        for width in (50, 100, 150, 200, 300, 400):
            pool.append((f"{kind} {width} мм", "м", trays))
    boards = "Щиты и боксы"
    for kind in ["Щит навесной", "Щит встраиваемый", "Бокс пластиковый", "ЩРН"]:
        for modules in (4, 6, 8, 12, 18, 24, 36):
            pool.append((f"{kind} на {modules} модулей", "шт", boards))
    fasten = "Крепёж и расходники"
    for kind in [
        "Дюбель-хомут",
        "Саморез по металлу",
        "Болт оцинкованный",
        "Стяжка нейлоновая",
        "Анкер клиновой",
    ]:
        for size in ("3х15", "4х20", "5х40", "6х60", "8х80", "10х100", "М6", "М8"):
            pool.append((f"{kind} {size}", "шт", fasten))
    return pool


def _noisy(name: str, rng: random.Random) -> str:
    """Produce a messy supplier/estimate-style variant of a canonical catalog name."""
    text = name
    if rng.random() < 0.5:
        text = text.replace("х", rng.choice(["x", "*", "х"]))
    if rng.random() < 0.25:
        text = text.replace(".", ",")
    if rng.random() < 0.3:
        text = text.replace("Автоматический выключатель", "Авт. выкл.")
    if rng.random() < 0.2:
        text = text.replace("(А)-LS", "")
    if rng.random() < 0.15:
        text = text.replace("Кабель ", "Каб. ")
    if rng.random() < 0.15:
        parts = text.split(" ")
        if len(parts) > 2:
            rng.shuffle(parts)
            text = " ".join(parts)
    if rng.random() < 0.12:
        text = f"{text} {rng.choice(['ГОСТ', '(бухта)', 'имп.', '100м'])}"
    return " ".join(text.split())


def _item_name(names: list[str], rng: random.Random) -> str:
    """A noisy catalog name, or (~10% of the time) an unrelated 'no match' row."""
    if rng.random() < 0.1:
        return rng.choice(_JUNK)
    return _noisy(rng.choice(names), rng)


def _money(rng: random.Random, low: float, high: float) -> Decimal:
    return Decimal(f"{rng.uniform(low, high):.2f}")


class Command(BaseCommand):
    help = "Generate a large, realistic dataset for manual/load testing."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("--catalog", type=int, default=1200)
        parser.add_argument("--suppliers", type=int, default=30)
        parser.add_argument("--pricelist-items", type=int, default=600)
        parser.add_argument("--projects", type=int, default=6)
        parser.add_argument("--estimates-per-project", type=int, default=2)
        parser.add_argument("--estimate-items", type=int, default=300)
        parser.add_argument("--seed", type=int, default=42)
        parser.add_argument("--clear", action="store_true", help="Wipe existing data first.")

    @transaction.atomic
    def handle(self, *args: Any, **opts: Any) -> None:
        rng = random.Random(opts["seed"])
        if opts["clear"]:
            for model in (Estimate, Project, PriceList, Supplier, CatalogProduct, ProductGroup):
                model.objects.all().delete()

        catalog_names = self._seed_catalog(rng, opts["catalog"])
        suppliers = self._seed_suppliers(rng, opts["suppliers"])
        self._seed_price_lists(rng, suppliers, catalog_names, opts["pricelist_items"])
        self._seed_projects(
            rng,
            catalog_names,
            opts["projects"],
            opts["estimates_per_project"],
            opts["estimate_items"],
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Готово: {CatalogProduct.objects.count()} товаров, "
                f"{Supplier.objects.count()} поставщиков, "
                f"{PriceListItem.objects.count()} позиций прайсов, "
                f"{EstimateItem.objects.count()} позиций смет."
            )
        )

    def _seed_catalog(self, rng: random.Random, count: int) -> list[str]:
        pool = _catalog_pool()
        rng.shuffle(pool)
        groups = {
            name: ProductGroup.objects.get_or_create(name=name)[0]
            for name in sorted({group for _n, _u, group in pool})
        }
        token = uuid.uuid4().hex[:6]  # unique per run, independent of --seed
        products: list[CatalogProduct] = []
        for i in range(count):
            name, unit, group = pool[i % len(pool)]
            cycle = i // len(pool)
            display = name if cycle == 0 else f"{name} (вар. {cycle + 1})"
            products.append(
                CatalogProduct(
                    article=f"G{token}-{i + 1:06d}", name=display, unit=unit, group=groups[group]
                )
            )
        CatalogProduct.objects.bulk_create(products, batch_size=1000)
        return [p.name for p in products]

    def _seed_suppliers(self, rng: random.Random, count: int) -> list[Supplier]:
        currencies = [code for code, _ in Supplier.Currency.choices]
        suppliers = [
            Supplier(
                name=f"ООО «{rng.choice(_COMPANY_STEMS)}-{rng.randint(1, 99)}»",
                inn=f"{rng.randint(1000000000, 9999999999)}",
                currency=rng.choice(currencies),
            )
            for _ in range(count)
        ]
        Supplier.objects.bulk_create(suppliers, batch_size=500)
        return suppliers

    def _seed_price_lists(
        self, rng: random.Random, suppliers: list[Supplier], names: list[str], per_list: int
    ) -> None:
        mapping = {"article": 0, "name": 1, "unit": 2, "price": 3}
        price_lists = [
            PriceList(
                supplier=supplier,
                source_filename=f"price_{supplier.pk}.xlsx",
                status="done",
                mapping=mapping,
                progress=100,
                total_rows=per_list,
                processed_rows=per_list,
            )
            for supplier in suppliers
        ]
        PriceList.objects.bulk_create(price_lists, batch_size=500)
        items = [
            PriceListItem(
                price_list=price_list,
                row_number=row,
                name=_item_name(names, rng),
                unit="шт",
                price=_money(rng, 10, 90000),
            )
            for price_list in price_lists
            for row in range(1, per_list + 1)
        ]
        PriceListItem.objects.bulk_create(items, batch_size=2000)

    def _seed_projects(
        self,
        rng: random.Random,
        names: list[str],
        projects: int,
        per_project: int,
        per_estimate: int,
    ) -> None:
        mapping = {
            "name": 0,
            "article": 1,
            "unit": 2,
            "quantity": 3,
            "material_price": 4,
            "installation_price": 5,
        }
        items: list[EstimateItem] = []
        for project_index in range(1, projects + 1):
            project = Project.objects.create(
                name=f"Проект №{project_index} — {rng.choice(_OBJECTS)}"
            )
            for est_index in range(1, per_project + 1):
                estimate = Estimate.objects.create(
                    project=project,
                    source_filename=f"smeta_{project_index}_{est_index}.xlsx",
                    status="done",
                    mapping=mapping,
                    progress=100,
                    total_rows=per_estimate,
                    processed_rows=per_estimate,
                )
                items.extend(
                    EstimateItem(
                        estimate=estimate,
                        row_number=row,
                        name=_item_name(names, rng),
                        unit="шт",
                        quantity=Decimal(f"{rng.uniform(1, 500):.3f}"),
                        material_price=_money(rng, 10, 90000),
                        installation_price=_money(rng, 0, 5000),
                    )
                    for row in range(1, per_estimate + 1)
                )
        EstimateItem.objects.bulk_create(items, batch_size=2000)
