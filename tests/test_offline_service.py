"""离线降级 AI 服务的检索与回答拼装测试。"""

from __future__ import annotations

from pathlib import Path

from education_rag.embedding import HashingHybridEmbedder
from web.offline_service import (
    OfflineEngine,
    build_index,
    compose_answer,
    compose_section_answer,
    group_by_section,
    missing_identifiers,
    rerank_sections,
    retrieve_sections,
    search,
    section_context,
    strip_context,
)


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


def test_group_by_section_merges_chunks_of_same_section():
    hits = [
        (0.9, {"chapter_path": "第1章 Java 基础语法 > 1.2 基本数据类型", "part": 0}),
        (0.8, {"chapter_path": "第1章 Java 基础语法 > 1.2 基本数据类型", "part": 1}),
        (0.7, {"chapter_path": "第1章 Java 基础语法 > 1.1 标识符", "part": 0}),
    ]
    sections = group_by_section(hits)
    assert len(sections) == 2
    assert len(sections["第1章 Java 基础语法 > 1.2 基本数据类型"]) == 2


def test_rerank_sections_rewards_repeated_evidence():
    hits = [
        (0.50, {"chapter_path": "A > 1.1 甲", "part": 0}),
        (0.49, {"chapter_path": "A > 1.2 乙", "part": 0}),
        (0.48, {"chapter_path": "A > 1.2 乙", "part": 1}),
        (0.47, {"chapter_path": "A > 1.2 乙", "part": 2}),
    ]
    ranked = rerank_sections(hits)
    assert ranked[0][1] == "A > 1.2 乙", "同一节命中多片时应当被提到最前"
    assert ranked[0][2][0][1]["part"] == 0, "节内片段按分数降序"


def test_rerank_sections_keeps_single_hit_order():
    hits = [(0.9, {"chapter_path": "A > 1.1 甲"}), (0.5, {"chapter_path": "A > 1.2 乙"})]
    ranked = rerank_sections(hits)
    assert [key for _, key, _ in ranked] == ["A > 1.1 甲", "A > 1.2 乙"]


def test_section_context_prefers_prose_and_keeps_order():
    items = [
        (0.9, {"part": 2, "content": "代码片段", "is_code": True}),
        (0.8, {"part": 1, "content": "第二段正文"}),
        (0.7, {"part": 0, "content": "第一段正文"}),
    ]
    context = section_context(items, max_chunks=2)
    assert "第一段正文" in context and "第二段正文" in context
    assert "代码片段" not in context, "正文足够时优先给正文"
    assert context.index("第一段正文") < context.index("第二段正文")


def test_compose_section_answer_merges_sibling_chunks(tmp_path: Path):
    corpus = _write_corpus(tmp_path / "corpus")
    records = build_index(corpus, HashingHybridEmbedder())
    sections = retrieve_sections(records, "Java 有哪些基本数据类型")
    assert sections
    answer, sources = compose_section_answer("Java 有哪些基本数据类型", sections)
    assert answer and "没有检索到" not in answer
    assert sources and sources[0]["source"] == "knowledge_base"


def test_strip_context_removes_code_metadata_line():
    text = "【Java 代码】Java 程序设计｜第 1 章 > 1.2（片段 2/3）\n```java\nint a = 1;\n```"
    cleaned = strip_context(text)
    assert "【Java 代码】" not in cleaned
    assert "片段 2/3" not in cleaned
    assert "int a = 1;" in cleaned


def test_engine_answer_has_no_metadata_prefix(tmp_path: Path):
    corpus = _write_corpus(tmp_path / "corpus")
    engine = OfflineEngine(corpus_dir=corpus)
    engine.load()
    result = engine.answer("写个 main 方法")
    assert "【Java 代码】" not in result["answer"]


def test_citations_only_cover_used_sections(tmp_path: Path):
    """引用必须来自真正拼进答案的小节：没有「此外」补充时，出处只能是最优小节。"""
    corpus = _write_corpus(tmp_path / "corpus")
    records = build_index(corpus, HashingHybridEmbedder())
    sections = retrieve_sections(records, "Java 有哪些基本数据类型")
    best = sections[0][1]
    answer, sources = compose_section_answer("Java 有哪些基本数据类型", sections)
    if "此外" not in answer:
        assert sources
        assert all(source["chapter_path"] == best for source in sources)


def test_compose_section_answer_handles_no_match():
    answer, sources = compose_section_answer("完全不相关的问题 xyz", [])
    assert "没有检索到" in answer
    assert sources == []


def test_missing_identifiers_flags_uncovered_term():
    context = "`HashMap` 用数组加链表存储键值对。"
    assert missing_identifiers("HashMap 和 Hashtable 有什么区别？", context) == ["hashtable"]
    # 上下文已覆盖时不应误报
    assert missing_identifiers("HashMap 怎么用？", context) == []
    # 中文问句没有标识符，不产生提示
    assert missing_identifiers("多态是什么意思？", "多态让调用方依赖抽象") == []


def test_answer_declares_uncovered_term(tmp_path: Path):
    """讲义没讲到 Hashtable 时，答案要说明「暂未讲到」，而不是装作答全了。"""
    corpus = _write_corpus(tmp_path / "corpus")
    records = build_index(corpus, HashingHybridEmbedder())
    sections = retrieve_sections(records, "HashMap 和 Hashtable 有什么区别")
    answer, _ = compose_section_answer("HashMap 和 Hashtable 有什么区别", sections)
    if "没有检索到" not in answer:
        assert "暂未讲到" in answer or "hashtable" not in answer.lower()


def _write_tiered_corpus(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "ch01-basics.md").write_text(
        "# 第1章 Java 基础语法\n\n## 1.1 标识符\n\n标识符不能以数字开头。\n",
        encoding="utf-8",
    )
    public = root / "public" / "javaguide"
    public.mkdir(parents=True, exist_ok=True)
    (public / "jvm-gc.md").write_text(
        "# JVM 垃圾回收\n\n## 垃圾收集算法\n\n常见的垃圾收集算法有标记-清除、复制和标记-整理。\n",
        encoding="utf-8",
    )
    return root


def test_build_index_marks_source_tier(tmp_path: Path):
    corpus = _write_tiered_corpus(tmp_path / "corpus")
    records = build_index(corpus, HashingHybridEmbedder())
    tiers = {record["source_tier"] for record in records}
    assert tiers == {"textbook", "extended"}
    assert any(record["source_tier"] == "extended" and "JVM" in record.get("chapter_path", "") for record in records)


def test_retrieve_sections_filters_by_tier(tmp_path: Path):
    corpus = _write_tiered_corpus(tmp_path / "corpus")
    records = build_index(corpus, HashingHybridEmbedder())

    extended = retrieve_sections(records, "垃圾收集算法有哪些", tier="extended")
    assert extended and all(record["source_tier"] == "extended" for _, _, items in extended for _, record in items)

    textbook = retrieve_sections(records, "垃圾收集算法有哪些", tier="textbook")
    assert textbook and all(record["source_tier"] == "textbook" for _, _, items in textbook for _, record in items)


def test_engine_answer_respects_scope(tmp_path: Path):
    corpus = _write_tiered_corpus(tmp_path / "corpus")
    engine = OfflineEngine(corpus_dir=corpus)
    engine.load()

    extended = engine.answer("标记-清除算法是什么", scope="extended")
    assert extended["sources"], "扩展范围应当能召回 JVM 资料"
    assert all(source["tier"] == "extended" for source in extended["sources"])

    textbook = engine.answer("标识符可以以数字开头吗", scope="textbook")
    assert textbook["sources"]
    assert all(source["tier"] == "textbook" for source in textbook["sources"])


def test_algorithm_corpus_is_skipped_by_default(tmp_path: Path, monkeypatch):
    corpus = _write_tiered_corpus(tmp_path / "corpus")
    algo = corpus / "public" / "algorithms" / "Sort.java.md"
    algo.parent.mkdir(parents=True, exist_ok=True)
    algo.write_text("# MergeSort\n\n```java\nclass MergeSort {}\n```\n", encoding="utf-8")

    monkeypatch.delenv("INDEX_PUBLIC_CODE", raising=False)
    default_records = build_index(corpus, HashingHybridEmbedder())
    assert not any("MergeSort" in record.get("chapter_path", "") for record in default_records)

    monkeypatch.setenv("INDEX_PUBLIC_CODE", "1")
    enabled_records = build_index(corpus, HashingHybridEmbedder())
    assert any("MergeSort" in record.get("chapter_path", "") for record in enabled_records)