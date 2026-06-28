"""Background parsing of price list files."""

from typing import Any

from celery import shared_task
from django.db import transaction

from apps.imports.constants import ImportStatus
from apps.imports.excel import iter_rows
from apps.imports.mapping import get_cell, to_decimal, to_text

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
