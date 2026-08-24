from education_rag.embedding import HashingHybridEmbedder
from education_rag.ingestion import EducationIngestionService
from education_rag.manifest import ImportManifest
from education_rag.repository import InMemoryVectorRepository


def test_same_hash_skips_and_changed_file_replaces(tmp_path):
    source = tmp_path / "课程介绍.md"
    source.write_text("# Python 课程\n\n## 基础\n\n变量与数据类型。", encoding="utf-8")
    repository = InMemoryVectorRepository()
    service = EducationIngestionService(
        repository=repository,
        embedder=HashingHybridEmbedder(),
        manifest=ImportManifest(tmp_path / "manifest.json"),
    )

    first = service.import_file(source)
    second = service.import_file(source)
    assert first["status"] == "imported"
    assert second["status"] == "skipped"
    first_ids = set(repository.records)

    source.write_text("# Python 课程\n\n## 基础\n\n变量、数据类型与函数。", encoding="utf-8")
    third = service.import_file(source)
    assert third["status"] == "imported"
    assert set(repository.records) != first_ids
    assert len(repository.records) == third["chunk_count"]
