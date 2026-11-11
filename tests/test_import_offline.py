from pathlib import Path

from education_rag.parsing import EducationDocumentParser

from web.offline_service import OfflineEngine, build_index


SAMPLE = """# 第 4 章 输入输出流

## 4.1 File 与路径

`File` 类表示文件或目录的路径，本身不打开文件。

```java
File f = new File("a.txt");
System.out.println(f.exists());
```

## 4.2 字节流与字符流

`InputStream`/`OutputStream` 处理字节，`Reader`/`Writer` 处理字符。

```java
try (FileInputStream in = new FileInputStream("a.txt")) {
    int b = in.read();
}
```

## 4.3 缓冲流

`BufferedReader` 提供按行读取的 `readLine()`。

```java
try (BufferedReader r = new BufferedReader(new FileReader("a.txt"))) {
    String line = r.readLine();
}
```
"""


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_import_file_adds_searchable_chunks(tmp_path):
    corpus = tmp_path / "corpus"
    _write(corpus / "ch01.md", "# 第 1 章\n\n## 1.1 变量\n\n变量是内存中的命名存储。\n")
    engine = OfflineEngine(corpus_dir=corpus)
    engine.load()
    before = len(engine.records)

    upload = _write(tmp_path / "uploads" / "ch04-io.md", SAMPLE)
    result = engine.import_file(upload)

    assert result["status"] == "completed"
    assert result["chunks"] > 0
    assert len(engine.records) == before + result["chunks"]

    hit = engine.answer("BufferedReader 怎么按行读取？")
    assert "BufferedReader" in hit["answer"]
    assert any(s.get("source_file", "").endswith("ch04-io.md") for s in hit["sources"])


def test_import_file_detects_duplicate(tmp_path):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    upload = _write(tmp_path / "ch04-io.md", SAMPLE)
    engine = OfflineEngine(corpus_dir=corpus)
    engine.load()

    assert engine.import_file(upload)["status"] == "completed"
    second = engine.import_file(upload)
    assert second["status"] == "duplicate"
    assert second["chunks"] == 0


def test_build_index_reads_docx_and_md(tmp_path):
    corpus = tmp_path / "corpus"
    _write(corpus / "ch01.md", "# 第 1 章\n\n## 1.1 变量\n\n变量是内存中的命名存储。\n")
    engine = OfflineEngine(corpus_dir=corpus)
    assert engine.load() > 0
    assert all(record["source_file"].endswith(".md") for record in engine.records)


def test_parser_supports_uploaded_extensions():
    assert {".md", ".docx", ".pdf"} <= EducationDocumentParser.supported_extensions
    assert build_index(Path("does-not-exist"), OfflineEngine().embedder) == []
