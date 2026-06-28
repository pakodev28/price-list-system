"""Price list API: upload, preview, background parse, catalog linking."""

from dataclasses import asdict

from django.conf import settings
from django.db.models import Count
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response

from apps.catalog.models import CatalogProduct
from apps.imports.excel import read_preview
from apps.matching.semantic import hybrid_shortlist
from apps.matching.shortlist import to_candidates

from .models import PriceList, PriceListItem
from .serializers import (
    ParseRequestSerializer,
    PriceListItemSerializer,
    PriceListSerializer,
    PriceListUploadSerializer,
)
from .tasks import auto_match_price_list, parse_price_list


class PriceListViewSet(viewsets.ModelViewSet):
    """Manage supplier price lists and their import lifecycle."""

    queryset = (
        PriceList.objects.select_related("supplier")
        .annotate(items_count=Count("items"))
        .order_by("-uploaded_at")
    )
    serializer_class = PriceListSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    filterset_fields = ["supplier", "status"]
    ordering_fields = ["uploaded_at"]

    def get_serializer_class(self):  # type: ignore[override]
        if self.action == "create":
            return PriceListUploadSerializer
        return PriceListSerializer

    @action(detail=True, methods=["get"])
    def preview(self, request: Request, pk: str | None = None) -> Response:
        """Return sheet/column structure and a sample of rows before parsing."""
        price_list = self.get_object()
        sheet = request.query_params.get("sheet") or None
        header_row_param = request.query_params.get("header_row")
        header_row = int(header_row_param) if header_row_param not in (None, "") else None
        try:
            preview = read_preview(price_list.file.path, sheet, header_row)
        except Exception as exc:  # noqa: BLE001 — bad/corrupt file -> 400, not 500
            return Response(
                {"detail": f"Не удалось прочитать файл: {exc}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(asdict(preview))

    @action(detail=True, methods=["post"])
    def parse(self, request: Request, pk: str | None = None) -> Response:
        """Persist the mapping and enqueue background parsing."""
        price_list = self.get_object()
        request_serializer = ParseRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        data = request_serializer.validated_data

        price_list.reset_job(
            mapping=data["mapping"], sheet=data["sheet"], header_row=data["header_row"]
        )
        price_list.save()

        async_result = parse_price_list.delay(price_list.id)
        price_list.task_id = async_result.id
        price_list.save(update_fields=["task_id"])
        return Response(PriceListSerializer(price_list).data, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=["post"], url_path="auto-match")
    def auto_match(self, request: Request, pk: str | None = None) -> Response:
        """Link items to catalog products above the confidence threshold (background)."""
        price_list = self.get_object()
        item_ids = request.data.get("item_ids") or None
        price_list.match_progress = 0
        price_list.save(update_fields=["match_progress"])
        auto_match_price_list.delay(price_list.id, item_ids)
        return Response(PriceListSerializer(price_list).data, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=["get"])
    def items(self, request: Request, pk: str | None = None) -> Response:
        """List parsed items of this price list."""
        price_list = self.get_object()
        page = self.paginate_queryset(price_list.items.select_related("catalog_product").all())
        serializer = PriceListItemSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class PriceListItemViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """Read price list items and link them to catalog products."""

    queryset = PriceListItem.objects.select_related("catalog_product").all()
    serializer_class = PriceListItemSerializer
    filterset_fields = ["price_list"]

    @action(detail=True, methods=["get"])
    def candidates(self, request: Request, pk: str | None = None) -> Response:
        """Return the fuzzy catalog shortlist for manual linking."""
        item = self.get_object()
        ranked = hybrid_shortlist(
            item.name, to_candidates(CatalogProduct.objects.all()), settings.MATCH_SHORTLIST_SIZE
        )
        return Response(
            [
                {"id": c.id, "article": c.article, "name": c.name, "score": round(score, 3)}
                for c, score in ranked
            ]
        )

    @action(detail=True, methods=["post"])
    def assign(self, request: Request, pk: str | None = None) -> Response:
        """Link this item to an existing catalog product."""
        item = self.get_object()
        product = get_object_or_404(CatalogProduct, pk=request.data.get("catalog_product"))
        item.catalog_product = product
        item.save(update_fields=["catalog_product"])
        return Response(PriceListItemSerializer(item).data)

    @action(detail=True, methods=["post"])
    def unlink(self, request: Request, pk: str | None = None) -> Response:
        """Remove the catalog link from this item."""
        item = self.get_object()
        item.catalog_product = None
        item.save(update_fields=["catalog_product"])
        return Response(PriceListItemSerializer(item).data)

    @action(detail=True, methods=["post"], url_path="create-product")
    def create_product(self, request: Request, pk: str | None = None) -> Response:
        """Create a catalog product from this position (hybrid catalog) and link it.

        Dedupes on the exact article when present.
        """
        item = self.get_object()
        article = item.article.strip()
        if article:
            product, _created = CatalogProduct.objects.get_or_create(
                article=article, defaults={"name": item.name, "unit": item.unit}
            )
        else:
            product = CatalogProduct.objects.create(
                article=f"GEN-{item.pk}", name=item.name, unit=item.unit
            )
        item.catalog_product = product
        item.save(update_fields=["catalog_product"])
        return Response(PriceListItemSerializer(item).data)
