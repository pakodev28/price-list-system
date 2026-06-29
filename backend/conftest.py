"""Shared pytest fixtures."""

import pytest


@pytest.fixture(autouse=True)
def _no_embed_on_create(settings) -> None:
    """Don't load the embedding model during tests.

    Embedding-on-create is on by default in real environments; tests that need it
    re-enable the flag and stub out the embedder.
    """
    settings.MATCH_EMBED_ON_CREATE = False
