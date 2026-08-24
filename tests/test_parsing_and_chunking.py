import zipfile

from education_rag.chunking import ChapterAwareSplitter
from education_rag.embedding import HashingHybridEmbedder
from education_rag.ingestion import EducationIngestionService
from education_rag.manifest import ImportManifest
from education_rag.models import EDUCATION_METADATA_FIELDS
from education_rag.parsing import EducationDocumentParser
from education_rag.repository import InMemoryVectorRepository


def _offline_import(path, tmp_path):
    repository = InMemoryVectorRepository()
    service = EducationIngestionService(
        repository=repository,
        embedder=HashingHybridEmbedder(),
        manifest=ImportManifest(tmp_path / f"{path.suffix}.manifest.json"),
    )
    result = service.import_file(path)
    assert result["status"] == "imported"
    assert result["chunk_count"] == len(repository.records) > 0


def test_markdown_chapter_metadata(tmp_path):
    path = tmp_path / "Python课程.md"
    path.write_text("# Python 入门\n\n## 函数\n\n函数使用 def 定义。\n\n## 列表\n\n列表保存有序数据。", encoding="utf-8")
    document = EducationDocumentParser().parse(path)
    chunks = ChapterAwareSplitter(max_chars=220, overlap_chars=20).split(document)
    assert {chunk.metadata.chapter_name for chunk in chunks} == {"函数", "列表"}
    assert "Python 入门 > 函数" in chunks[0].metadata.chapter_path
    assert set(EDUCATION_METADATA_FIELDS) <= set(chunks[0].to_record())
    _offline_import(path, tmp_path)


def test_question_bank_metadata(tmp_path):
    path = tmp_path / "题目资料.md"
    path.write_text(
        "# 题目\n\n## Python 基础题库\n\n### python_bank_q001\n\n"
        "- **题型**: 单选题\n- **题干**: 函数用什么关键字定义？\n- **答案**: def",
        encoding="utf-8",
    )
    chunk = ChapterAwareSplitter(max_chars=300, overlap_chars=20).split(EducationDocumentParser().parse(path))[0]
    assert chunk.metadata.content_type == "question"
    assert chunk.metadata.question_bank_name == "Python 基础题库"
    assert chunk.metadata.question_id == "python_bank_q001"
    assert chunk.metadata.question_type == "单选题"


def test_docx_heading_is_parsed(tmp_path):
    path = tmp_path / "深度学习课程.docx"
    document_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>
      <w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>神经网络</w:t></w:r></w:p>
      <w:p><w:r><w:t>反向传播用于计算梯度。</w:t></w:r></w:p>
    </w:body></w:document>"""
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", document_xml)
    parsed = EducationDocumentParser().parse(path)
    assert parsed.sections[0].heading_path == ["神经网络"]
    assert "反向传播" in parsed.sections[0].text
    _offline_import(path, tmp_path)


def _write_minimal_text_pdf(path):
    stream = b"BT /F1 12 Tf 72 720 Td (Python function course material) Tj ET"
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, body in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{number} 0 obj\n".encode() + body + b"\nendobj\n")
    xref = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode())
    output.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    )
    path.write_bytes(output)


def test_pdf_pages_are_parsed_with_page_number(tmp_path):
    path = tmp_path / "算法讲义.pdf"
    _write_minimal_text_pdf(path)
    parsed = EducationDocumentParser().parse(path)
    assert parsed.sections[0].page_number == 1
    assert parsed.sections[0].heading_path[-1] == "第 1 页"
    assert "Python function" in parsed.sections[0].text
    _offline_import(path, tmp_path)
