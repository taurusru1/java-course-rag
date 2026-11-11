from __future__ import annotations

from pathlib import Path

from .chunking import ChapterAwareSplitter, CodeAwareSplitter
from .embedding import BGEM3Embedder, HybridEmbedder, attach_embeddings
from .manifest import ImportManifest
from .parsing import EducationDocumentParser
from .repository import VectorRepository


class EducationIngestionService:
    def __init__(
        self,
        repository: VectorRepository,
        parser: EducationDocumentParser | None = None,
        splitter: ChapterAwareSplitter | None = None,
        embedder: HybridEmbedder | None = None,
        manifest: ImportManifest | None = None,
    ):
        self.repository = repository
        self.parser = parser or EducationDocumentParser()
        self.splitter = splitter or CodeAwareSplitter()
        self.embedder = embedder or BGEM3Embedder()
        self.manifest = manifest or ImportManifest()

    def import_file(self, file_path: str | Path) -> dict:
        path = Path(file_path).resolve()
        file_hash = self.parser.calculate_hash(path)
        if self.manifest.has_same_hash(path.name, file_hash):
            return {"status": "skipped", "source_file": path.name, "file_hash": file_hash, "chunk_count": 0}

        document = self.parser.parse(path)
        chunks = self.splitter.split(document)
        if not chunks:
            raise ValueError(f"资料未生成有效切片：{path.name}")
        attach_embeddings(chunks, self.embedder)
        chunk_ids = self.repository.replace_source(document.source_file, chunks)
        self.manifest.record(document.source_file, document.file_hash, len(chunk_ids))
        return {
            "status": "imported",
            "source_file": document.source_file,
            "file_hash": document.file_hash,
            "chunk_count": len(chunk_ids),
            "chunk_ids": chunk_ids,
        }
