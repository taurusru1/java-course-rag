from __future__ import annotations

import hashlib
import re
from pathlib import Path

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
