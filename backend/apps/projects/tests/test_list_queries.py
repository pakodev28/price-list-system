"""List endpoints must not issue per-row queries (N+1 regression guard)."""

import pytest
from rest_framework.test import APIClient

from apps.projects.factories import EstimateFactory, ProjectFactory

pytestmark = pytest.mark.django_db


def test_estimate_list_query_count_is_constant(django_assert_max_num_queries) -> None:
    project = ProjectFactory()
    EstimateFactory.create_batch(5, project=project)
    client = APIClient()

    with django_assert_max_num_queries(4):
        response = client.get("/api/estimates/")

    assert response.status_code == 200
    assert response.json()["count"] == 5
