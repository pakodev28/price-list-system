"""Background parsing of price list files."""

import concurrent.futures
from typing import Any

from celery import shared_task
from django.conf import settings
from django.db import transaction

from apps.catalog.models import CatalogProduct
from apps.imports.constants import ImportStatus
from apps.imports.excel import iter_rows
from apps.imports.mapping import get_cell, to_decimal, to_text
from apps.matching.service import MatchingService
from apps.matching.shortlist import to_candidates

from .models import PriceList, PriceListItem

_BATCH_SIZE = 500


@shared_task
def parse_price_list(price_list_id: int) -> dict[str, int]:
    """Parse a price list file into items, reporting progress on the record.

    Rows are built in memory (collecting per-row errors), then the item set is
    swapped atomically so a mid-parse failure never leaves a half-parsed list.
    """
    price_list = PriceList.objects.get(pk=price_list_id)
    try:
        price_list.status = ImportStatus.PARSING
        price_list.progress = 0
        price_list.processed_rows = 0
        price_list.save(update_fields=["status", "progress", "processed_rows"])

        rows = list(
            iter_rows(price_list.file.path, price_list.sheet or None, price_list.header_row)
        )
        price_list.total_rows = len(rows)
        price_list.save(update_fields=["total_rows"])

        items, errors = _build_items(price_list, rows)

        with transaction.atomic():
            price_list.items.all().delete()
            PriceListItem.objects.bulk_create(items, batch_size=_BATCH_SIZE)

        price_list.processed_rows = len(items)
        price_list.row_errors = errors
        price_list.progress = 100
        price_list.status = ImportStatus.DONE
        price_list.save(update_fields=["processed_rows", "row_errors", "progress", "status"])
    except Exception as exc:  # noqa: BLE001 — record failure, then re-raise
        price_list.status = ImportStatus.FAILED
        price_list.error = str(exc)
        price_list.save(update_fields=["status", "error"])
        raise
    return {"created": len(items)}


def _build_items(
    price_list: PriceList, rows: list[list[Any]]
) -> tuple[list[PriceListItem], list[dict[str, object]]]:
    """Build item objects from rows, collecting per-row errors and progress."""
    mapping = price_list.mapping
    total = len(rows) or 1
    items: list[PriceListItem] = []
    errors: list[dict[str, object]] = []
    for index, row in enumerate(rows, start=1):
        try:
            name = to_text(get_cell(row, mapping.get("name")))
            if not name:
                continue  # skip blank rows
            items.append(
                PriceListItem(
                    price_list=price_list,
                    row_number=index,
                    article=to_text(get_cell(row, mapping.get("article"))),
                    name=name,
                    unit=to_text(get_cell(row, mapping.get("unit"))),
                    price=to_decimal(get_cell(row, mapping.get("price"))),
                )
            )
        except Exception as exc:  # noqa: BLE001 — collect row error and continue
            errors.append({"row": index, "message": str(exc)})
        if index % _BATCH_SIZE == 0:
            price_list.progress = min(99, int(index / total * 100))
            price_list.save(update_fields=["progress"])
    return items, errors


@shared_task
def auto_match_price_list(price_list_id: int, item_ids: list[int] | None = None) -> dict[str, int]:
    """Link price list items to catalog products above the confidence threshold.

    When ``item_ids`` is given, only those items are processed; otherwise all of them.
    Unlike estimates this only links *confident* matches (price lists carry no
    per-item confidence display); weaker rows are left for manual linking.
    """
    price_list = PriceList.objects.get(pk=price_list_id)
    candidates = to_candidates(CatalogProduct.objects.all())
    service = MatchingService()
    queryset = price_list.items.all()
    if item_ids:
        queryset = queryset.filter(pk__in=item_ids)
    items = list(queryset)
    total = len(items) or 1

    price_list.match_progress = 0
    price_list.save(update_fields=["match_progress"])

    linked = 0
    done = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=settings.MATCH_CONCURRENCY) as pool:
        futures = {
            pool.submit(service.match, item.name, item.article, candidates): item for item in items
        }
        for future in concurrent.futures.as_completed(futures):
            item = futures[future]
            outcome = future.result()
            if outcome.product_id is not None and outcome.confidence >= service.threshold:
                item.catalog_product_id = outcome.product_id
                item.save(update_fields=["catalog_product"])
                linked += 1
            done += 1
            if done % 10 == 0 or done == total:
                price_list.match_progress = min(100, int(done / total * 100))
                price_list.save(update_fields=["match_progress"])

    price_list.match_progress = 100
    price_list.save(update_fields=["match_progress"])
    return {"linked": linked}
