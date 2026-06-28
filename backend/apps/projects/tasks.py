"""Background tasks: estimate parsing and AI auto-matching."""

from typing import Any

from celery import shared_task
from django.db import transaction

from apps.catalog.models import CatalogProduct
from apps.imports.constants import ImportStatus
from apps.imports.excel import iter_rows
from apps.imports.mapping import get_cell, to_decimal, to_text
from apps.matching.service import MatchingService
from apps.matching.shortlist import to_candidates

from .models import Estimate, EstimateItem

_BATCH_SIZE = 500


@shared_task
def parse_estimate(estimate_id: int) -> dict[str, int]:
    """Parse an estimate file into items with an atomic swap (see parse_price_list)."""
    estimate = Estimate.objects.get(pk=estimate_id)
    try:
        estimate.status = ImportStatus.PARSING
        estimate.progress = 0
        estimate.processed_rows = 0
        estimate.save(update_fields=["status", "progress", "processed_rows"])

        rows = list(iter_rows(estimate.file.path, estimate.sheet or None, estimate.header_row))
        estimate.total_rows = len(rows)
        estimate.save(update_fields=["total_rows"])

        items, errors = _build_items(estimate, rows)

        with transaction.atomic():
            estimate.items.all().delete()
            EstimateItem.objects.bulk_create(items, batch_size=_BATCH_SIZE)

        estimate.processed_rows = len(items)
        estimate.row_errors = errors
        estimate.progress = 100
        estimate.status = ImportStatus.DONE
        estimate.save(update_fields=["processed_rows", "row_errors", "progress", "status"])
    except Exception as exc:  # noqa: BLE001
        estimate.status = ImportStatus.FAILED
        estimate.error = str(exc)
        estimate.save(update_fields=["status", "error"])
        raise
    return {"created": len(items)}


def _build_items(
    estimate: Estimate, rows: list[list[Any]]
) -> tuple[list[EstimateItem], list[dict[str, object]]]:
    """Build estimate items from rows, collecting per-row errors and progress."""
    mapping = estimate.mapping
    total = len(rows) or 1
    items: list[EstimateItem] = []
    errors: list[dict[str, object]] = []
    for index, row in enumerate(rows, start=1):
        try:
            name = to_text(get_cell(row, mapping.get("name")))
            if not name:
                continue
            items.append(
                EstimateItem(
                    estimate=estimate,
                    row_number=index,
                    name=name,
                    article=to_text(get_cell(row, mapping.get("article"))),
                    unit=to_text(get_cell(row, mapping.get("unit"))),
                    quantity=to_decimal(get_cell(row, mapping.get("quantity"))),
                    material_price=to_decimal(get_cell(row, mapping.get("material_price"))),
                    installation_price=to_decimal(get_cell(row, mapping.get("installation_price"))),
                )
            )
        except Exception as exc:  # noqa: BLE001 — collect row error and continue
            errors.append({"row": index, "message": str(exc)})
        if index % _BATCH_SIZE == 0:
            estimate.progress = min(99, int(index / total * 100))
            estimate.save(update_fields=["progress"])
    return items, errors


@shared_task
def auto_match_estimate(estimate_id: int) -> dict[str, int]:
    """Match every estimate item against the catalog, reporting progress.

    Items are saved one-by-one on purpose: matching is dominated by per-item LLM
    latency, and incremental saves let the UI stream results as they land.
    """
    estimate = Estimate.objects.get(pk=estimate_id)
    candidates = to_candidates(CatalogProduct.objects.all())
    service = MatchingService()
    items = list(estimate.items.all())
    total = len(items) or 1

    estimate.match_progress = 0
    estimate.save(update_fields=["match_progress"])

    matched = 0
    for position, item in enumerate(items, start=1):
        outcome = service.match(item.name, item.article, candidates)
        item.catalog_product_id = outcome.product_id
        item.confidence = outcome.confidence
        item.match_source = EstimateItem.MatchSource.AUTO
        item.match_status = (
            EstimateItem.MatchStatus.MATCHED
            if outcome.product_id is not None
            else EstimateItem.MatchStatus.NO_MATCH
        )
        item.save(update_fields=["catalog_product", "confidence", "match_source", "match_status"])
        matched += 1 if outcome.product_id is not None else 0
        if position % 10 == 0 or position == total:
            estimate.match_progress = min(100, int(position / total * 100))
            estimate.save(update_fields=["match_progress"])

    estimate.match_progress = 100
    estimate.save(update_fields=["match_progress"])
    return {"matched": matched}
