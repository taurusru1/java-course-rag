from __future__ import annotations

import hashlib
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from .models import DocumentSection, ParsedDocument


class UnsupportedDocumentError(ValueError):
    pass


class EducationDocumentParser:
    """将 PDF、Markdown、DOCX 统一解析为带章节路径的文本段。"""

    supported_extensions = {".pdf", ".md", ".markdown", ".docx"}

    def parse(self, file_path: str | Path) -> ParsedDocument:
        path = Path(file_path).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"资料文件不存在：{path}")
        suffix = path.suffix.lower()
        if suffix not in self.supported_extensions:
            raise UnsupportedDocumentError(f"不支持的资料类型：{suffix}")

        file_hash = self.calculate_hash(path)
        if suffix in {".md", ".markdown"}:
            sections = self._parse_markdown(path.read_text(encoding="utf-8"))
        elif suffix == ".docx":
            sections = self._parse_docx(path)
        else:
            sections = self._parse_pdf(path)

        sections = [section for section in sections if section.text.strip()]
        if not sections:
            raise ValueError(f"未从资料中解析出可检索文本：{path.name}")
        return ParsedDocument(str(path), path.name, file_hash, sections)

    @staticmethod
    def calculate_hash(path: Path, block_size: int = 1024 * 1024) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            while block := stream.read(block_size):
                digest.update(block)
        return digest.hexdigest()

    def _parse_markdown(self, text: str) -> list[DocumentSection]:
        headings: list[str] = []
        buffer: list[str] = []
        sections: list[DocumentSection] = []

        def flush() -> None:
            content = "\n".join(buffer).strip()
            if content:
                sections.append(DocumentSection(content, headings.copy()))
            buffer.clear()

        for line in text.replace("\r\n", "\n").split("\n"):
            match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
            if match:
                flush()
                level = len(match.group(1))
                title = match.group(2).strip().strip("#").strip()
                headings[:] = headings[: level - 1]
                headings.append(title)
            else:
                buffer.append(line)
        flush()
        return sections

    def _parse_docx(self, path: Path) -> list[DocumentSection]:
        with zipfile.ZipFile(path) as archive:
            document_xml = archive.read("word/document.xml")
            styles_xml = archive.read("word/styles.xml") if "word/styles.xml" in archive.namelist() else b""
        root = ET.fromstring(document_xml)
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        style_levels = self._docx_style_levels(styles_xml, ns)
        headings: list[str] = []
        page = 1
        sections: list[DocumentSection] = []
        buffer: list[str] = []
        section_page = page

        def flush() -> None:
            nonlocal section_page
            content = "\n".join(buffer).strip()
            if content:
                sections.append(DocumentSection(content, headings.copy(), section_page))
            buffer.clear()
            section_page = page

        for paragraph in root.findall(".//w:body//w:p", ns):
            text = "".join(node.text or "" for node in paragraph.findall(".//w:t", ns)).strip()
            style_node = paragraph.find("./w:pPr/w:pStyle", ns)
            style = "" if style_node is None else style_node.attrib.get(f"{{{ns['w']}}}val", "")
            heading_match = re.search(r"(?:Heading|标题)\s*([1-6])", style, re.IGNORECASE)
            heading_level = style_levels.get(style) or (int(heading_match.group(1)) if heading_match else 0)
            if heading_level and text:
                flush()
                level = heading_level
                headings[:] = headings[: level - 1]
                headings.append(text)
            elif text:
                buffer.append(text)

            page_breaks = len(paragraph.findall(".//w:br[@w:type='page']", ns))
            rendered_breaks = len(paragraph.findall(".//w:lastRenderedPageBreak", ns))
            if page_breaks or rendered_breaks:
                flush()
                page += max(1, page_breaks + rendered_breaks)
                section_page = page
        flush()
        return sections

    @staticmethod
    def _docx_style_levels(styles_xml: bytes, ns: dict[str, str]) -> dict[str, int]:
        if not styles_xml:
            return {}
        root = ET.fromstring(styles_xml)
        namespace = ns["w"]
        result: dict[str, int] = {}
        for style in root.findall("w:style", ns):
            style_id = style.attrib.get(f"{{{namespace}}}styleId", "")
            name_node = style.find("w:name", ns)
            name = "" if name_node is None else name_node.attrib.get(f"{{{namespace}}}val", "")
            outline = style.find(".//w:outlineLvl", ns)
            if outline is not None:
                value = int(outline.attrib.get(f"{{{namespace}}}val", "9"))
                if 0 <= value <= 5:
                    result[style_id] = value + 1
                    continue
            match = re.search(r"(?:Heading|标题)\s*([1-6])", name, re.IGNORECASE)
            if match:
                result[style_id] = int(match.group(1))
        return result

    def _parse_pdf(self, path: Path) -> list[DocumentSection]:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("解析 PDF 需要安装 pypdf，请执行 uv sync") from exc

        sections: list[DocumentSection] = []
        reader = PdfReader(str(path))
        for page_number, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if text:
                sections.append(DocumentSection(text, [path.stem, f"第 {page_number} 页"], page_number))
        return sections
