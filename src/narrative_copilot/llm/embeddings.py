"""
Embedding providers for dense vector retrieval.
"""

import asyncio
import hashlib
import os
from typing import Any

import numpy as np

from narrative_copilot.llm.provider import EmbeddingProvider

__all__ = [
    "DeterministicEmbeddingStub",
    "EmbeddingProvider",
    "SentenceTransformerEmbeddingProvider",
]


class SentenceTransformerEmbeddingProvider:
    """
    Standard high-quality local semantic embedding provider using SentenceTransformers.
    Pinned to 'all-MiniLM-L6-v2' (dimension 384) for fast, accurate CPU evaluation.
    """

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        self._model_name = model_name
        self._model: Any = None
        self._dimension = 384

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model_name

    def _get_model(self) -> Any:
        if self._model is None:
            mode = os.environ.get("EMBEDDING_MODE", "").lower().strip()
            if (
                mode == "deterministic_fixture"
                or os.environ.get("USE_DETERMINISTIC_EMBEDDINGS") == "1"
            ):
                self._model = DeterministicEmbeddingStub(dimension=self._dimension)
                return self._model

            # Full reference mode: load genuine SentenceTransformer
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self._model_name, device="cpu")
        return self._model

    def encode(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        model = self._get_model()
        if isinstance(model, DeterministicEmbeddingStub):
            return model.encode(texts)
        embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return embeddings.tolist()  # type: ignore[no-any-return]

    async def aencode(self, texts: list[str]) -> list[list[float]]:
        return await asyncio.to_thread(self.encode, texts)


class DeterministicEmbeddingStub:
    """
    Deterministic zero-network embedding generator for fast unit tests.
    Generates reproducible 384-dimensional unit-norm vectors from text hashes.
    NOTE: Never substituted silently for benchmark semantic scores.
    """

    def __init__(self, dimension: int = 384) -> None:
        self._dimension = dimension
        self._model_name = "deterministic-stub-v1"

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model_name

    def encode(self, texts: list[str]) -> list[list[float]]:
        results: list[list[float]] = []
        for text in texts:
            words = text.lower().split()
            if not words:
                vec = np.zeros(self._dimension, dtype=np.float32)
                vec[0] = 1.0
                results.append(vec.tolist())
                continue

            vec = np.zeros(self._dimension, dtype=np.float32)
            for w in words:
                seed = int(hashlib.sha256(w.encode("utf-8")).hexdigest()[:8], 16)
                rng = np.random.default_rng(seed)
                token_vec = rng.standard_normal(self._dimension).astype(np.float32)
                vec += token_vec

            norm = float(np.linalg.norm(vec))
            if norm > 1e-6:
                vec /= norm
            results.append(vec.tolist())
        return results

    async def aencode(self, texts: list[str]) -> list[list[float]]:
        return await asyncio.to_thread(self.encode, texts)
