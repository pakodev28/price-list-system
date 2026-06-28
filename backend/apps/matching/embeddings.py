"""Local multilingual static embeddings (model2vec — pure numpy, no onnxruntime).

The model is loaded lazily as a thread-safe singleton, so importing this module
(for ``encode``/``decode``) never pulls the model into memory.
"""

import threading
from typing import TYPE_CHECKING

import numpy as np

MODEL_NAME = "minishlab/potion-multilingual-128M"

_model = None
_lock = threading.Lock()

if TYPE_CHECKING:
    from model2vec import StaticModel


def get_model() -> "StaticModel":
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                from model2vec import StaticModel

                _model = StaticModel.from_pretrained(MODEL_NAME)
    return _model


def embed_texts(texts: list[str]) -> np.ndarray:
    """Return L2-normalized embeddings (cosine similarity becomes a dot product)."""
    vectors = np.asarray(get_model().encode(texts), dtype=np.float32)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / np.clip(norms, 1e-9, None)


def encode(vector: np.ndarray) -> bytes:
    return vector.astype(np.float32).tobytes()


def decode(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32)


def embed_catalog(batch_size: int = 512) -> int:
    """Embed catalog products that have no embedding yet; returns the count embedded."""
    from apps.catalog.models import CatalogProduct

    pending = list(CatalogProduct.objects.filter(embedding__isnull=True).only("id", "name"))
    for start in range(0, len(pending), batch_size):
        chunk = pending[start : start + batch_size]
        vectors = embed_texts([p.name for p in chunk])
        for product, vector in zip(chunk, vectors, strict=True):
            product.embedding = encode(vector)
        CatalogProduct.objects.bulk_update(chunk, ["embedding"])
    return len(pending)
