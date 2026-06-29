"""Generate a large, realistic dataset for manual and load testing.

Domain: import logistics China → Russia and customs clearance. The catalog holds
freight/customs services and imported-goods categories; estimates and price lists
reference them with *noisy* names (abbreviations, reordered words, dropped codes)
plus ~10% unrelated rows, so matching has realistic work to do.

Usage (inside the backend container):
    python manage.py seed_large
    python manage.py seed_large --catalog 1000 --suppliers 20
    python manage.py seed_large --clear            # wipe existing data first
"""

import random
import re
import uuid
from decimal import Decimal
from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import CatalogProduct, ProductGroup
from apps.pricelists.models import PriceList, PriceListItem
from apps.projects.models import Estimate, EstimateItem, Project
from apps.suppliers.models import Supplier

_COMPANY_STEMS = [
    "ВЭД-Логистик",
    "КитайКарго",
    "ТрансАзия",
    "Силк Роуд Логистикс",
    "ДальКонтейнер",
    "ПрофТаможня",
    "Восток-Запад",
    "Глобал Фрахт",
    "Азия Импорт",
    "Карго Экспресс",
    "ТаможняСервис",
    "ПрофВЭД",
]
_OBJECTS = [
    "Поставка электроники (контракт CN-2026-014)",
    "Импорт текстиля из Гуанчжоу",
    "Партия бытовой техники",
    "Контейнер автозапчастей",
    "Сборный груз из Иу",
    "Поставка мебели",
    "Импорт инструмента",
    "Партия игрушек",
]
_JUNK = [
    "Прочие расходы",
    "Комиссия банка за платёж",
    "Курьерская доставка документов",
    "Перевод инвойса и упаковочного листа",
    "Представительские расходы",
    "Непредвиденные расходы",
]
_GOODS = [
    ("Смартфон", "8517130000"),
    ('Ноутбук 15.6"', "8471300000"),
    ("Планшет", "8471300000"),
    ("Кроссовки текстильные", "6404110000"),
    ("Куртка зимняя", "6201400000"),
    ("Футболка хлопковая", "6109100000"),
    ("Игрушка пластиковая", "9503009900"),
    ("Тормозные колодки", "8708301000"),
    ("Аккумулятор автомобильный", "8507100000"),
    ("Светодиодная лампа", "8539500000"),
    ("Пылесос бытовой", "8508110000"),
    ("Микроволновая печь", "8516500000"),
    ("Наушники беспроводные", "8518300000"),
    ("Стул офисный", "9401300000"),
    ("Стол письменный", "9403100000"),
    ("Шуруповёрт аккумуляторный", "8467211000"),
    ("Набор отвёрток", "8205400000"),
    ("Кофемашина", "8516710000"),
    ("Робот-пылесос", "8508110000"),
    ('Монитор 27"', "8528520000"),
    ("Клавиатура механическая", "8471605000"),
    ("Power bank 20000 мА·ч", "8507600000"),
    ("Велосипед горный", "8712003000"),
    ("Электросамокат", "8711600100"),
    ("Термос стальной", "9617000000"),
    ("Посуда керамическая (набор)", "6912008500"),
    ("Гирлянда LED", "9405400000"),
    ("Рюкзак городской", "4202129100"),
    ("Зонт автоматический", "6601100000"),
    ("Кабель USB-C", "8544429000"),
]


def _catalog_pool() -> list[tuple[str, str, str]]:
    """Canonical ``(name, unit, group)`` catalog entries — logistics & customs."""
    pool: list[tuple[str, str, str]] = []

    sea = "Морской фрахт"
    sea_routes = [
        "Шанхай–Владивосток",
        "Нинбо–Восточный",
        "Циндао–Новороссийск",
        "Шэньчжэнь–Санкт-Петербург",
        "Гуанчжоу–Владивосток",
        "Тяньцзинь–Восточный",
        "Сямынь–Новороссийск",
        "Далянь–Владивосток",
    ]
    for route in sea_routes:
        for cont in ("20DC", "40DC", "40HC", "LCL сборный"):
            pool.append((f"Морской фрахт {route}, {cont}", "конт.", sea))

    air = "Авиаперевозки"
    air_routes = [
        "Гуанчжоу–Москва",
        "Шанхай–Москва",
        "Шэньчжэнь–Екатеринбург",
        "Иу–Москва",
        "Пекин–Новосибирск",
        "Гонконг–Москва",
    ]
    for route in air_routes:
        for weight in ("до 45 кг", "45–100 кг", "100–300 кг", "300–500 кг", "от 500 кг"):
            pool.append((f"Авиаперевозка {route}, {weight}", "кг", air))

    rail = "Ж/д перевозки"
    rail_routes = [
        "Чунцин–Москва",
        "Сиань–Москва",
        "Чэнду–Электроугли",
        "Иу–Ворсино",
        "Сучжоу–Москва",
        "Далянь–Москва",
    ]
    for route in rail_routes:
        for cont in ("20DC", "40HC", "сборный"):
            pool.append((f"Ж/д перевозка {route}, {cont}", "конт.", rail))

    auto = "Автодоставка по РФ"
    auto_routes = [
        "Владивосток–Москва",
        "Новороссийск–Москва",
        "СПб–Москва",
        "Восточный–Екатеринбург",
        "Москва–Казань",
        "Москва–Новосибирск",
        "Владивосток–Хабаровск",
        "Москва–Краснодар",
    ]
    for route in auto_routes:
        for truck in ("тент 20т", "реф 20т", "контейнеровоз"):
            pool.append((f"Автодоставка {route}, {truck}", "рейс", auto))

    duty = "Таможенные платежи"
    categories = [
        "электроника",
        "текстиль",
        "обувь",
        "игрушки",
        "автозапчасти",
        "мебель",
        "бытовая техника",
        "инструмент",
        "косметика",
        "посуда",
    ]
    for cat in categories:
        pool.append((f"Таможенная пошлина: {cat}", "усл.", duty))
    for fee in ("НДС 20%", "Таможенный сбор", "Утилизационный сбор", "Акциз"):
        pool.append((fee, "усл.", duty))

    clearance = "Таможенное оформление"
    for service in [
        "Услуги таможенного брокера (1 ДТ)",
        "Дополнительный лист ДТ",
        "Электронное декларирование",
        "Корректировка таможенной стоимости (КТС)",
        "Предварительное решение по классификации",
        "Подбор кода ТН ВЭД",
        "Организация таможенного досмотра",
        "Выпуск под обеспечение",
    ]:
        pool.append((service, "усл.", clearance))

    cert = "Сертификация"
    cert_docs = [
        "Сертификат соответствия ТР ТС",
        "Декларация соответствия ТР ТС",
        "Отказное письмо",
        "Свидетельство о госрегистрации (СГР)",
        "Протокол испытаний",
        "Сертификат происхождения СТ-1",
    ]
    for doc in cert_docs:
        for cat in categories[:5]:
            pool.append((f"{doc} ({cat})", "усл.", cert))

    warehouse = "Склад и СВХ"
    for service in [
        "Хранение на СВХ (1 сутки)",
        "Хранение на складе (паллетоместо/сутки)",
        "ПРР контейнера 20'",
        "ПРР контейнера 40'",
        "Маркировка «Честный знак» (1 ед.)",
        "Стикеровка (1 ед.)",
        "Паллетирование",
        "Пересчёт груза",
        "Кросс-докинг",
    ]:
        pool.append((service, "усл.", warehouse))

    insurance = "Страхование"
    for service in [
        "Страхование груза (0.2% от стоимости)",
        "Страхование контейнерной перевозки",
        "Страхование авиагруза",
        "Страхование сборного груза",
    ]:
        pool.append((service, "усл.", insurance))

    goods = "Товары (импорт)"
    for name, code in _GOODS:
        pool.append((f"{name} (ТН ВЭД {code})", "шт", goods))

    return pool


def _noisy(name: str, rng: random.Random) -> str:
    """Produce a messy supplier/estimate-style variant of a canonical catalog name."""
    text = name
    abbreviations = [
        ("Морской фрахт", "Мор. фрахт"),
        ("Авиаперевозка", "Авиа"),
        ("Ж/д перевозка", "ЖД"),
        ("Автодоставка", "Авто"),
        ("Таможенная пошлина:", "Пошлина"),
        ("Услуги таможенного брокера", "Брокер"),
        ("контейнер", "конт."),
        ("Хранение", "Хран."),
    ]
    for src, dst in abbreviations:
        if rng.random() < 0.35:
            text = text.replace(src, dst)
    if rng.random() < 0.3:
        text = text.replace("–", "-")
    if rng.random() < 0.2:
        text = re.sub(r"\s*\(ТН ВЭД \d+\)", "", text)
    if rng.random() < 0.15:
        parts = text.split(" ")
        if len(parts) > 2:
            rng.shuffle(parts)
            text = " ".join(parts)
    if rng.random() < 0.12:
        text = f"{text} {rng.choice(['срочно', '(КНР)', 'предоплата', 'до двери'])}"
    return " ".join(text.split())


def _item_name(names: list[str], rng: random.Random) -> str:
    """A noisy catalog name, or (~10% of the time) an unrelated 'no match' row."""
    if rng.random() < 0.1:
        return rng.choice(_JUNK)
    return _noisy(rng.choice(names), rng)


def _money(rng: random.Random, low: float, high: float) -> Decimal:
    return Decimal(f"{rng.uniform(low, high):.2f}")


class Command(BaseCommand):
    help = "Generate a large, realistic logistics/customs dataset for manual testing."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("--catalog", type=int, default=400)
        parser.add_argument("--suppliers", type=int, default=10)
        parser.add_argument("--pricelist-items", type=int, default=200)
        parser.add_argument("--projects", type=int, default=2)
        parser.add_argument("--estimates-per-project", type=int, default=2)
        parser.add_argument("--estimate-items", type=int, default=100)
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
                f"Готово: {CatalogProduct.objects.count()} позиций каталога, "
                f"{Supplier.objects.count()} поставщиков, "
                f"{PriceListItem.objects.count()} позиций прайсов, "
                f"{EstimateItem.objects.count()} позиций смет."
            )
        )

    def _seed_catalog(self, rng: random.Random, count: int) -> list[str]:
        """Create ``count`` catalog products, cycling the pool with variant suffixes.

        Articles are prefixed with a per-run ``uuid`` token (independent of
        ``--seed``) so repeated runs never collide on the unique article field.
        """
        pool = _catalog_pool()
        rng.shuffle(pool)
        groups = {
            name: ProductGroup.objects.get_or_create(name=name)[0]
            for name in sorted({group for _n, _u, group in pool})
        }
        token = uuid.uuid4().hex[:6]
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
                unit="усл.",
                price=_money(rng, 500, 850000),
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
                name=f"Сделка №{project_index} — {rng.choice(_OBJECTS)}"
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
                        unit="усл.",
                        quantity=Decimal(f"{rng.uniform(1, 50):.3f}"),
                        material_price=_money(rng, 500, 850000),
                        installation_price=_money(rng, 0, 50000),
                    )
                    for row in range(1, per_estimate + 1)
                )
        EstimateItem.objects.bulk_create(items, batch_size=2000)
