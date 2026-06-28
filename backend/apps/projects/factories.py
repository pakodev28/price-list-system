"""Test factories for projects and estimates."""

import factory

from .models import Estimate, Project


class ProjectFactory(factory.django.DjangoModelFactory[Project]):
    class Meta:
        model = Project

    name = factory.Sequence(lambda n: f"Проект {n}")


class EstimateFactory(factory.django.DjangoModelFactory[Estimate]):
    class Meta:
        model = Estimate

    project = factory.SubFactory(ProjectFactory)
    source_filename = "estimate.xlsx"
    mapping = {
        "name": 0,
        "article": 1,
        "unit": 2,
        "quantity": 3,
        "material_price": 4,
        "installation_price": 5,
    }
