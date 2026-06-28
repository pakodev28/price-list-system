"""Supplier API."""

from rest_framework import viewsets

from .models import Supplier
from .serializers import SupplierSerializer


class SupplierViewSet(viewsets.ModelViewSet):
    """CRUD for suppliers with name/INN search."""

    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    search_fields = ["name", "inn"]
    ordering_fields = ["name", "created_at"]
