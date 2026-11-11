"""离线降级 AI 服务的检索与回答拼装测试。"""

from __future__ import annotations

from pathlib import Path

from education_rag.embedding import HashingHybridEmbedder
from web.offline_service import OfflineEngine, build_index, compose_answer, search


def _write_corpus(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "ch01-basics.md").write_text(
        "# 第1章 Java 基础语法\n\n"
        "## 1.1 标识符\n\n"
        "标识符由字母、数字、下划线和美元符号组成，不能以数字开头。\n\n"
        "## 1.2 基本数据类型\n\n"
        "Java 有 8 种基本数据类型：byte、short、int、long、float、double、char、boolean。\n\n"
        "```java\npublic class Demo {\n    public static void main(String[] args) {\n        int a = 1;\n    }\n}\n```\n",
        encoding="utf-8",
    )
    return root


def test_build_index_produces_chunks_with_metadata(tmp_path: Path):
    corpus = _write_corpus(tmp_path / "corpus")
    records = build_index(corpus, HashingHybridEmbedder())
    assert records, "应当至少生成一个片段"
    assert all("dense_vector" in record for record in records)
    assert any(record.get("is_code") for record in records)
    assert any("Java 基础语法" in record.get("chapter_path", "") for record in records)


def test_search_ranks_relevant_chapter_first(tmp_path: Path):
    corpus = _write_corpus(tmp_path / "corpus")
    records = build_index(corpus, HashingHybridEmbedder())
    hits = search(records, "int 是什么数据类型")
    assert hits
    assert "数据类型" in hits[0][1]["chapter_path"] or "int" in hits[0][1]["content"]


def test_compose_answer_returns_citation(tmp_path: Path):
    corpus = _write_corpus(tmp_path / "corpus")
    records = build_index(corpus, HashingHybridEmbedder())
    hits = search(records, "基本数据类型有哪些")
    answer, sources = compose_answer("基本数据类型有哪些", hits)
    assert "byte" in answer or "8 种" in answer
    assert sources and sources[0]["source"] == "knowledge_base"
    assert sources[0]["source_file"] == "ch01-basics.md"


def test_compose_answer_handles_no_match():
    answer, sources = compose_answer("完全不相关的问题 xyz", [])
    assert "没有检索到" in answer
    assert sources == []


def test_engine_answer_records_session(tmp_path: Path):
    corpus = _write_corpus(tmp_path / "corpus")
    engine = OfflineEngine(corpus_dir=corpus)
    assert engine.load() > 0
    result = engine.answer("Java 有哪些基本数据类型", "s-1")
    assert result["sources"]
    assert len(engine.sessions["s-1"]) == 2
    assert engine.sessions["s-1"][0]["role"] == "user"
