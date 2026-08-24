from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol

from .models import EducationChunk


class HybridEmbedder(Protocol):
    def embed_documents(self, texts: list[str]) -> dict[str, list]: ...


class BGEM3Embedder:
    def embed_documents(self, texts: list[str]) -> dict[str, list]:
        from utils.embedding_utils import generate_embeddings

        return generate_embeddings(texts)


class HashingHybridEmbedder:
    """无模型、无网络的确定性 mock，仅用于自动化测试与评测演示。"""

    def __init__(self, dimensions: int = 128):
        self.dimensions = dimensions

    @staticmethod
    def tokens(text: str) -> list[str]:
        latin = re.findall(r"[A-Za-z0-9_]+", text.lower())
        chinese = [char for char in text if "\u4e00" <= char <= "\u9fff"]
        return latin + chinese

    def embed_documents(self, texts: list[str]) -> dict[str, list]:
        dense_vectors: list[list[float]] = []
        sparse_vectors: list[dict[int, float]] = []
        for text in texts:
            counts: dict[int, float] = {}
            dense = [0.0] * self.dimensions
            for token in self.tokens(text):
                index = int(hashlib.sha256(token.encode("utf-8")).hexdigest()[:8], 16) % self.dimensions
                counts[index] = counts.get(index, 0.0) + 1.0
                dense[index] += 1.0
            norm = math.sqrt(sum(value * value for value in dense)) or 1.0
            dense_vectors.append([value / norm for value in dense])
            sparse_vectors.append(counts)
        return {"dense": dense_vectors, "sparse": sparse_vectors}


def attach_embeddings(chunks: list[EducationChunk], embedder: HybridEmbedder, batch_size: int = 8) -> None:
    for start in range(0, len(chunks), batch_size):
        batch = chunks[start : start + batch_size]
        vectors = embedder.embed_documents([chunk.embedding_text() for chunk in batch])
        for index, chunk in enumerate(batch):
            chunk.dense_vector = vectors["dense"][index]
            chunk.sparse_vector = vectors["sparse"][index]
