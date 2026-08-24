from __future__ import annotations

from utils.milvus_utils import escape_milvus_string


FILTERABLE_FIELDS = {
    "content_type", "course_name", "project_name", "chapter_name",
    "question_bank_name", "question_id", "question_type", "source_file", "page_number",
}


def build_milvus_filter(filters: dict | None) -> str | None:
    """只允许白名单字段，避免把用户输入直接拼入 Milvus 表达式。"""
    expressions: list[str] = []
    for field, value in (filters or {}).items():
        if field not in FILTERABLE_FIELDS or value in (None, "", []):
            continue
        if field == "page_number":
            expressions.append(f"{field} == {int(value)}")
        elif isinstance(value, list):
            values = ", ".join(f'"{escape_milvus_string(str(item))}"' for item in value)
            expressions.append(f"{field} in [{values}]")
        else:
            expressions.append(f'{field} == "{escape_milvus_string(str(value))}"')
    return " and ".join(expressions) or None
