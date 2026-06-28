"""Catalog API."""

from rest_framework import viewsets

from .models import CatalogProduct, ProductGroup
from .serializers import CatalogProductSerializer, ProductGroupSerializer


class ProductGroupViewSet(viewsets.ModelViewSet):
    """CRUD for product groups."""

    queryset = ProductGroup.objects.all()
    serializer_class = ProductGroupSerializer
    search_fields = ["name"]


class CatalogProductViewSet(viewsets.ModelViewSet):
    """CRUD for catalog products with search and group filtering."""

    queryset = CatalogProduct.objects.select_related("group").all()
    serializer_class = CatalogProductSerializer
    search_fields = ["article", "name"]
    filterset_fields = ["group"]
    ordering_fields = ["name", "article", "created_at"]
