from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


EDUCATION_METADATA_FIELDS = (
    "content_type",
    "course_name",
    "project_name",
    "chapter_name",
    "chapter_path",
    "knowledge_points",
    "question_bank_name",
    "question_id",
    "question_type",
    "source_file",
    "page_number",
)


@dataclass(slots=True)
class EducationMetadata:
    content_type: str = "course_document"
    course_name: str = ""
    project_name: str = ""
    chapter_name: str = ""
    chapter_path: str = ""
    knowledge_points: list[str] = field(default_factory=list)
    question_bank_name: str = ""
    question_id: str = ""
    question_type: str = ""
    source_file: str = ""
    page_number: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class DocumentSection:
    text: str
    heading_path: list[str]
    page_number: int = 0


@dataclass(slots=True)
class ParsedDocument:
    source_path: str
    source_file: str
    file_hash: str
    sections: list[DocumentSection]


@dataclass(slots=True)
class EducationChunk:
    chunk_id: str
    content: str
    metadata: EducationMetadata
    file_hash: str
    part: int = 0
    dense_vector: list[float] | None = None
    sparse_vector: dict[int, float] | None = None

    def embedding_text(self) -> str:
        prefix = " / ".join(
            value
            for value in (
                self.metadata.course_name,
                self.metadata.project_name,
                self.metadata.chapter_path,
                "、".join(self.metadata.knowledge_points),
            )
            if value
        )
        return f"{prefix}\n{self.content}" if prefix else self.content

    def to_record(self) -> dict[str, Any]:
        result = {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "file_hash": self.file_hash,
            "part": self.part,
            **self.metadata.to_dict(),
        }
        if self.dense_vector is not None:
            result["dense_vector"] = self.dense_vector
        if self.sparse_vector is not None:
            result["sparse_vector"] = self.sparse_vector
        return result


def citation_from_record(record: dict[str, Any]) -> dict[str, Any]:
    """生成前端可直接展示的知识库引用。"""
    return {
        "source": "knowledge_base",
        "chunk_id": record.get("chunk_id", ""),
        "course_name": record.get("course_name", ""),
        "project_name": record.get("project_name", ""),
        "chapter_name": record.get("chapter_name", ""),
        "chapter_path": record.get("chapter_path", ""),
        "source_file": record.get("source_file", ""),
        "page_number": record.get("page_number", 0),
    }
