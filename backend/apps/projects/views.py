"""Project, estimate and estimate-item APIs."""

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
from apps.matching.semantic import retrieve
from apps.matching.shortlist import to_candidates

from .models import Estimate, EstimateItem, Project
from .serializers import (
    EstimateItemSerializer,
    EstimateSerializer,
    EstimateUploadSerializer,
    ParseEstimateRequestSerializer,
    ProjectSerializer,
)
from .tasks import auto_match_estimate, parse_estimate


class ProjectViewSet(viewsets.ModelViewSet):
    """CRUD for projects."""

    queryset = Project.objects.annotate(estimates_count=Count("estimates")).order_by("-created_at")
    serializer_class = ProjectSerializer
    search_fields = ["name"]
    ordering_fields = ["name", "created_at"]


class EstimateViewSet(viewsets.ModelViewSet):
    """Manage estimates: upload, preview, parse, auto-match."""

    queryset = (
        Estimate.objects.select_related("project")
        .annotate(items_count=Count("items"))
        .order_by("-uploaded_at")
    )
    serializer_class = EstimateSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    filterset_fields = ["project", "status"]
    ordering_fields = ["uploaded_at"]

    def get_serializer_class(self):  # type: ignore[override]
        if self.action == "create":
            return EstimateUploadSerializer
        return EstimateSerializer

    @action(detail=True, methods=["get"])
    def preview(self, request: Request, pk: str | None = None) -> Response:
        estimate = self.get_object()
        sheet = request.query_params.get("sheet") or None
        header_row_param = request.query_params.get("header_row")
        header_row = int(header_row_param) if header_row_param not in (None, "") else None
        try:
            preview = read_preview(estimate.file.path, sheet, header_row)
        except Exception as exc:  # noqa: BLE001
            return Response(
                {"detail": f"Не удалось прочитать файл: {exc}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(asdict(preview))

    @action(detail=True, methods=["post"])
    def parse(self, request: Request, pk: str | None = None) -> Response:
        estimate = self.get_object()
        request_serializer = ParseEstimateRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        data = request_serializer.validated_data

        estimate.reset_job(
            mapping=data["mapping"], sheet=data["sheet"], header_row=data["header_row"]
        )
        estimate.save()
        async_result = parse_estimate.delay(estimate.id)
        estimate.task_id = async_result.id
        estimate.save(update_fields=["task_id"])
        return Response(EstimateSerializer(estimate).data, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=["post"], url_path="auto-match")
    def auto_match(self, request: Request, pk: str | None = None) -> Response:
        estimate = self.get_object()
        item_ids = request.data.get("item_ids") or None
        estimate.match_progress = 0
        estimate.save(update_fields=["match_progress"])
        auto_match_estimate.delay(estimate.id, item_ids)
        return Response(EstimateSerializer(estimate).data, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=["get"])
    def items(self, request: Request, pk: str | None = None) -> Response:
        estimate = self.get_object()
        page = self.paginate_queryset(estimate.items.select_related("catalog_product").all())
        serializer = EstimateItemSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class EstimateItemViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """Read estimate items and apply manual matching decisions."""

    queryset = EstimateItem.objects.select_related("catalog_product").all()
    serializer_class = EstimateItemSerializer
    filterset_fields = ["estimate", "match_status"]

    @action(detail=True, methods=["post"])
    def assign(self, request: Request, pk: str | None = None) -> Response:
        """Manually link this item to a catalog product."""
        item = self.get_object()
        product = get_object_or_404(CatalogProduct, pk=request.data.get("catalog_product"))
        item.catalog_product = product
        item.match_status = EstimateItem.MatchStatus.MATCHED
        item.match_source = EstimateItem.MatchSource.MANUAL
        item.confidence = 1.0
        item.save(update_fields=["catalog_product", "match_status", "match_source", "confidence"])
        return Response(EstimateItemSerializer(item).data)

    @action(detail=True, methods=["post"], url_path="no-match")
    def no_match(self, request: Request, pk: str | None = None) -> Response:
        """Mark this item as having no catalog correspondence."""
        item = self.get_object()
        item.catalog_product = None
        item.match_status = EstimateItem.MatchStatus.NO_MATCH
        item.match_source = EstimateItem.MatchSource.MANUAL
        item.confidence = None
        item.save(update_fields=["catalog_product", "match_status", "match_source", "confidence"])
        return Response(EstimateItemSerializer(item).data)

    @action(detail=True, methods=["get"])
    def candidates(self, request: Request, pk: str | None = None) -> Response:
        """Return the fuzzy catalog shortlist for manual selection."""
        item = self.get_object()
        ranked = retrieve(
            item.name, to_candidates(CatalogProduct.objects.all()), settings.MATCH_SHORTLIST_SIZE
        )
        return Response(
            [
                {"id": c.id, "article": c.article, "name": c.name, "score": round(score, 3)}
                for c, score in ranked
            ]
        )
