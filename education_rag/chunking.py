from __future__ import annotations

import hashlib
import re
from dataclasses import replace
from pathlib import Path

from .code_chunking import (
    CodeBlock,
    _split_by_lines,
    detect_language,
    extract_symbols,
    parse_markdown_units,
    split_java_code,
)
from .models import DocumentSection, EducationChunk, EducationMetadata, ParsedDocument


class ChapterAwareSplitter:
    def __init__(self, max_chars: int = 1500, overlap_chars: int = 160):
        if max_chars < 200 or overlap_chars < 0 or overlap_chars >= max_chars:
            raise ValueError("切片参数不合法")
        self.max_chars = max_chars
        self.overlap_chars = overlap_chars

    def split(self, document: ParsedDocument) -> list[EducationChunk]:
        chunks: list[EducationChunk] = []
        for section in document.sections:
            metadata = self._infer_metadata(document, section)
            for part, content in enumerate(self._split_text(section.text)):
                raw_id = "|".join(
                    (document.source_file, document.file_hash, metadata.chapter_path, str(part), content)
                )
                chunk_id = hashlib.sha256(raw_id.encode("utf-8")).hexdigest()[:32]
                chunks.append(EducationChunk(chunk_id, content, metadata, document.file_hash, part))
        return chunks

    def _split_text(self, text: str) -> list[str]:
        paragraphs = [item.strip() for item in re.split(r"\n\s*\n|(?<=[。！？；])\s+", text) if item.strip()]
        if not paragraphs:
            return []
        result: list[str] = []
        current = ""
        for paragraph in paragraphs:
            if len(paragraph) > self.max_chars:
                if current:
                    result.append(current)
                    current = ""
                start = 0
                while start < len(paragraph):
                    result.append(paragraph[start : start + self.max_chars])
                    start += self.max_chars - self.overlap_chars
                continue
            candidate = f"{current}\n\n{paragraph}".strip()
            if current and len(candidate) > self.max_chars:
                result.append(current)
                overlap = current[-self.overlap_chars :] if self.overlap_chars else ""
                current = f"{overlap}\n\n{paragraph}".strip()
            else:
                current = candidate
        if current:
            result.append(current)
        return result

    def _infer_metadata(self, document: ParsedDocument, section: DocumentSection) -> EducationMetadata:
        source_path = Path(document.source_path)
        source_stem = source_path.stem
        heading_path = [h.strip() for h in section.heading_path if h.strip()]
        chapter_name = heading_path[-1] if heading_path else source_stem
        chapter_path = " > ".join(heading_path) or source_stem
        combined = f"{chapter_path}\n{section.text[:1200]}"

        is_question = bool(re.search(r"题库|题型|题干|_q\d+", combined, re.IGNORECASE))
        is_project = "项目文档" in document.source_path or "项目" in source_stem
        is_intro = "课程介绍" in source_stem or any(h == "课程" for h in heading_path)
        content_type = (
            "question" if is_question else "project_material" if is_project else "course_intro" if is_intro else "course_document"
        )

        question_id_match = re.search(r"([A-Za-z0-9_\-]+_q\d+)", combined, re.IGNORECASE)
        question_type_match = re.search(r"(?:\*\*)?题型(?:\*\*)?\s*[:：]\s*([^\n]+)", combined)
        bank_name = ""
        for heading in heading_path:
            if "题库" in heading:
                bank_name = heading

        project_name = source_stem if is_project else ""
        if is_question or is_project:
            course_name = ""
        elif is_intro:
            candidates = [h for h in heading_path if h not in {"课程", "题目"} and "题库" not in h]
            course_name = candidates[0] if candidates else source_stem
        else:
            course_name = source_stem

        knowledge_points = []
        for name in heading_path[-3:]:
            if name not in {course_name, bank_name, "课程", "题目"} and name not in knowledge_points:
                knowledge_points.append(name)

        return EducationMetadata(
            content_type=content_type,
            course_name=course_name,
            project_name=project_name,
            chapter_name=chapter_name,
            chapter_path=chapter_path,
            knowledge_points=knowledge_points,
            question_bank_name=bank_name,
            question_id=question_id_match.group(1) if question_id_match else "",
            question_type=question_type_match.group(1).strip() if question_type_match else "",
            source_file=document.source_file,
            page_number=section.page_number,
        )


class CodeAwareSplitter(ChapterAwareSplitter):
    """代码感知切分（创新点 C1）。

    与父类的区别：
    - 围栏代码块是原子单元，不会被正文段落挤断；
    - 超长代码块优先在类成员边界切分，并给每片补上类声明与结构标签；
    - 代码片段的元数据额外记录 is_code / code_language / code_symbols。
    """

    def split(self, document: ParsedDocument) -> list[EducationChunk]:
        chunks: list[EducationChunk] = []
        for section in document.sections:
            metadata = self._infer_metadata(document, section)
            for part, (content, is_code, language, symbols) in enumerate(
                self._split_section(section.text, metadata)
            ):
                part_metadata = replace(
                    metadata,
                    is_code=is_code,
                    code_language=language,
                    code_symbols=symbols,
                )
                raw_id = "|".join(
                    (document.source_file, document.file_hash, part_metadata.chapter_path, str(part), content)
                )
                chunk_id = hashlib.sha256(raw_id.encode("utf-8")).hexdigest()[:32]
                chunks.append(EducationChunk(chunk_id, content, part_metadata, document.file_hash, part))
        return chunks

    def _split_section(
        self, text: str, metadata: EducationMetadata
    ) -> list[tuple[str, bool, str, list[str]]]:
        pieces: list[tuple[str, bool, str, list[str]]] = []
        prose: list[str] = []
        for kind, payload in parse_markdown_units(text):
            if kind == "text":
                prose.append(str(payload))
                continue
            pieces.extend(self._prose_pieces(prose))
            prose = []
            pieces.extend(self._code_pieces(payload, metadata))  # type: ignore[arg-type]
        pieces.extend(self._prose_pieces(prose))
        return [piece for piece in pieces if piece[0].strip()]

    def _prose_pieces(self, prose: list[str]) -> list[tuple[str, bool, str, list[str]]]:
        if not prose:
            return []
        merged = "\n\n".join(prose).strip()
        if not merged:
            return []
        return [(part, False, "", []) for part in self._split_text(merged)]

    def _code_pieces(
        self, block: CodeBlock, metadata: EducationMetadata
    ) -> list[tuple[str, bool, str, list[str]]]:
        language = detect_language(block.code, block.language)
        symbols = extract_symbols(block.code, language)
        context = self._code_context(metadata, language, symbols)
        fence = f"```{block.language or (language if language != 'text' else '')}"
        if len(context) + len(block.code) + len(fence) + 4 <= self.max_chars:
            return [(f"{context}\n{fence}\n{block.code}\n```", True, language, symbols)]

        budget = max(300, self.max_chars - len(context) - len(fence) - 12)
        parts = (
            split_java_code(block.code, budget, self.overlap_chars)
            if language == "java"
            else _split_by_lines(block.code, budget, self.overlap_chars)
        )
        total = len(parts)
        result: list[tuple[str, bool, str, list[str]]] = []
        for index, part in enumerate(parts, start=1):
            label = f"{context}（片段 {index}/{total}）" if total > 1 else context
            result.append((f"{label}\n{fence}\n{part}\n```", True, language, symbols))
        return result

    @staticmethod
    def _code_context(metadata: EducationMetadata, language: str, symbols: list[str]) -> str:
        location = metadata.chapter_path or metadata.source_file
        label = {"java": "Java 代码", "python": "Python 代码"}.get(language, "代码")
        structure = "、".join(symbols) if symbols else "未识别结构"
        prefix = f"{metadata.course_name}｜" if metadata.course_name else ""
        return f"【{label}】{prefix}{location}｜结构：{structure}"
