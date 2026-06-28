"""Price list API: upload, preview, background parse."""

from dataclasses import asdict

from django.db.models import Count
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response

from apps.imports.excel import read_preview

from .models import PriceList
from .serializers import (
    ParseRequestSerializer,
    PriceListItemSerializer,
    PriceListSerializer,
    PriceListUploadSerializer,
)
from .tasks import parse_price_list


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

    @action(detail=True, methods=["get"])
    def items(self, request: Request, pk: str | None = None) -> Response:
        """List parsed items of this price list."""
        price_list = self.get_object()
        page = self.paginate_queryset(price_list.items.all())
        serializer = PriceListItemSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)
