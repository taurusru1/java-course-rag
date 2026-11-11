from __future__ import annotations

import re

from education_rag.chunking import ChapterAwareSplitter, CodeAwareSplitter
from education_rag.code_chunking import detect_language, extract_symbols, parse_markdown_units, split_java_code
from education_rag.embedding import HashingHybridEmbedder
from education_rag.ingestion import EducationIngestionService
from education_rag.manifest import ImportManifest
from education_rag.models import EDUCATION_METADATA_FIELDS
from education_rag.parsing import EducationDocumentParser
from education_rag.repository import InMemoryVectorRepository

JAVA_SAMPLE = """```java
public class ListDemo {
    public static void main(String[] args) {
        List<String> names = new ArrayList<>();
        names.add("Tom");
        names.add("Jerry");
        System.out.println(names);
    }
}
```"""


def _parse(tmp_path, text: str, name: str = "Java 课程笔记.md"):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return EducationDocumentParser().parse(path)


def _big_java_class(methods: int = 3) -> str:
    body_lines = [
        "        int total = 0;",
        "        for (int i = 0; i < values.length; i++) {",
        "            total += values[i] * 2 + i;",
        "            total = total % 1000 + values[i];",
        "            total = total * 2 - values[i];",
        "        }",
        "        List<String> buffer = new ArrayList<>();",
        "        buffer.add(\"value-\" + total);",
        "        buffer.add(\"size-\" + values.length);",
        "        String joined = String.join(\",\", buffer);",
        "        System.out.println(joined);",
        "        total += joined.length();",
        "        return total;",
    ]
    methods_text = []
    for index in range(methods):
        methods_text.append(
            f"    public int compute{index}(int[] values) {{\n" + "\n".join(body_lines) + "\n    }"
        )
    return "public class BigDemo {\n" + "\n\n".join(methods_text) + "\n}"


def test_code_block_is_atomic_and_tagged(tmp_path):
    document = _parse(tmp_path, f"# 集合框架\n\n## List 的使用\n\n下面是创建列表的示例：\n\n{JAVA_SAMPLE}\n\n运行后输出列表内容。")
    chunks = CodeAwareSplitter(max_chars=1500, overlap_chars=100).split(document)

    code_chunks = [chunk for chunk in chunks if chunk.metadata.is_code]
    assert len(code_chunks) == 1
    code_chunk = code_chunks[0]
    assert "```java" in code_chunk.content and "public class ListDemo" in code_chunk.content
    assert code_chunk.content.rstrip().endswith("```")
    assert code_chunk.metadata.code_language == "java"
    assert "ListDemo" in code_chunk.metadata.code_symbols
    assert "main" in code_chunk.metadata.code_symbols

    prose_chunks = [chunk for chunk in chunks if not chunk.metadata.is_code]
    assert prose_chunks and all("```" not in chunk.content for chunk in prose_chunks)


def test_oversized_class_is_split_on_member_boundaries(tmp_path):
    code = _big_java_class(methods=3)
    document = _parse(tmp_path, f"# 面向对象\n\n## 方法设计\n\n```java\n{code}\n```")
    chunks = CodeAwareSplitter(max_chars=900, overlap_chars=0).split(document)
    code_chunks = [chunk for chunk in chunks if chunk.metadata.is_code]

    assert len(code_chunks) >= 3
    assert all(len(chunk.content) <= 900 for chunk in code_chunks)
    assert all("public class BigDemo" in chunk.content for chunk in code_chunks)
    for index in range(3):
        owners = [chunk for chunk in code_chunks if f"public int compute{index}(" in chunk.content]
        assert len(owners) == 1, f"compute{index} 的方法体应只出现在一个片段中"
    assert all("片段" in chunk.content for chunk in code_chunks)


def test_split_java_code_keeps_class_header():
    pieces = split_java_code(_big_java_class(methods=2), max_chars=700, overlap_chars=0)
    assert len(pieces) >= 2
    assert all("public class BigDemo" in piece for piece in pieces)
    assert all(len(piece) <= 700 for piece in pieces)


def test_language_detection_and_symbols():
    assert detect_language("public class A { void run() {} }", "") == "java"
    assert detect_language("def run():\n    pass", "") == "python"
    assert detect_language("```", "py") == "python"
    assert detect_language("plain text", "") == "text"
    symbols = extract_symbols("public class Node { public int size() { return 0; } }", "java")
    assert symbols[:2] == ["Node", "size"]


def test_markdown_units_keep_fences_balanced():
    units = parse_markdown_units(f"前言\n\n{JAVA_SAMPLE}\n\n结语")
    kinds = [kind for kind, _ in units]
    assert kinds == ["text", "code", "text"]
    code_unit = units[1][1]
    assert "```" not in code_unit.code


def test_chapter_splitter_can_still_be_used(tmp_path):
    document = _parse(tmp_path, f"# 集合\n\n## List\n\n{JAVA_SAMPLE}")
    chunks = ChapterAwareSplitter(max_chars=1500, overlap_chars=100).split(document)
    assert chunks and all(not chunk.metadata.is_code for chunk in chunks)


def test_metadata_carries_code_fields(tmp_path):
    document = _parse(tmp_path, f"# 集合\n\n## List\n\n{JAVA_SAMPLE}")
    chunk = CodeAwareSplitter(max_chars=1500, overlap_chars=100).split(document)[0]
    record = chunk.to_record()
    assert set(EDUCATION_METADATA_FIELDS) <= set(record)
    assert record["is_code"] is True
    assert record["code_language"] == "java"
    assert isinstance(record["code_symbols"], list)
    assert not re.search(r"\n\s*$", chunk.content)


def test_default_ingestion_uses_code_aware_splitter(tmp_path):
    path = tmp_path / "Java 课程.md"
    path.write_text(f"# 集合框架\n\n## List\n\n{JAVA_SAMPLE}", encoding="utf-8")
    repository = InMemoryVectorRepository()
    service = EducationIngestionService(
        repository=repository,
        embedder=HashingHybridEmbedder(),
        manifest=ImportManifest(tmp_path / "manifest.json"),
    )
    result = service.import_file(path)
    assert result["status"] == "imported"
    records = repository.all()
    assert any(record["is_code"] for record in records)
    assert all("is_code" in record for record in records)
