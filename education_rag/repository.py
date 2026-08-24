from __future__ import annotations

from copy import deepcopy
from typing import Protocol

from .models import EducationChunk


class VectorRepository(Protocol):
    def replace_source(self, source_file: str, chunks: list[EducationChunk]) -> list[str]: ...


class InMemoryVectorRepository:
    """离线测试仓储；行为与真实仓储一致：按来源原子替换，不产生重复切片。"""

    def __init__(self):
        self.records: dict[str, dict] = {}

    def replace_source(self, source_file: str, chunks: list[EducationChunk]) -> list[str]:
        self.records = {
            key: value for key, value in self.records.items() if value.get("source_file") != source_file
        }
        for chunk in chunks:
            self.records[chunk.chunk_id] = deepcopy(chunk.to_record())
        return [chunk.chunk_id for chunk in chunks]

    def all(self) -> list[dict]:
        return list(self.records.values())
