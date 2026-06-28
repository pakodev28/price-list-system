"""Supplier API tests."""

import pytest
from rest_framework.test import APIClient

from apps.suppliers.factories import SupplierFactory
from apps.suppliers.models import Supplier

pytestmark = pytest.mark.django_db


def test_create_supplier() -> None:
    client = APIClient()
    payload = {"name": "ООО Ромашка", "inn": "7701234567", "currency": "RUB"}
    response = client.post("/api/suppliers/", payload, format="json")
    assert response.status_code == 201
    assert Supplier.objects.filter(name="ООО Ромашка").exists()


def test_reject_invalid_inn() -> None:
    client = APIClient()
    response = client.post(
        "/api/suppliers/", {"name": "X", "inn": "123", "currency": "RUB"}, format="json"
    )
    assert response.status_code == 400
    assert "inn" in response.json()


def test_search_by_name() -> None:
    SupplierFactory(name="Альфа")
    SupplierFactory(name="Бета")
    client = APIClient()
    response = client.get("/api/suppliers/", {"search": "Альф"})
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["name"] == "Альфа"
