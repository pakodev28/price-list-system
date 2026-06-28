"""Estimate parse-request validation (mapping guard)."""

from apps.projects.serializers import ParseEstimateRequestSerializer


def test_rejects_mapping_without_name() -> None:
    serializer = ParseEstimateRequestSerializer(data={"mapping": {"article": 1}})
    assert not serializer.is_valid()
    assert "mapping" in serializer.errors


def test_accepts_mapping_with_name() -> None:
    serializer = ParseEstimateRequestSerializer(data={"mapping": {"name": 0}})
    assert serializer.is_valid(), serializer.errors
