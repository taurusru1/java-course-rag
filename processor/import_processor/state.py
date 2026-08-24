"""教育资料导入 LangGraph 状态。"""

import copy
from typing import Any, TypedDict


class ImportGraphState(TypedDict, total=False):
    task_id: str
    import_file_path: str
    file_dir: str
    file_title: str
    source_file: str
    file_hash: str
    document_type: str
    parsed_document: Any
    chunks: list[dict]
    import_status: str
    skipped: bool
    chunk_count: int


GRAPH_DEFAULT_STATE: ImportGraphState = {
    "task_id": "", "import_file_path": "", "file_dir": "", "file_title": "",
    "source_file": "", "file_hash": "", "document_type": "", "chunks": [],
    "import_status": "pending", "skipped": False, "chunk_count": 0,
}


def get_default_state() -> ImportGraphState:
    return copy.deepcopy(GRAPH_DEFAULT_STATE)
