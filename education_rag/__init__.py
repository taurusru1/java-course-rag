"""教育领域 RAG 的可复用核心能力。"""

from .chunking import ChapterAwareSplitter
from .ingestion import EducationIngestionService
from .models import EDUCATION_METADATA_FIELDS, EducationChunk, EducationMetadata
from .parsing import EducationDocumentParser

__all__ = [
    "ChapterAwareSplitter",
    "EducationDocumentParser",
    "EducationIngestionService",
    "EducationChunk",
    "EducationMetadata",
    "EDUCATION_METADATA_FIELDS",
]
