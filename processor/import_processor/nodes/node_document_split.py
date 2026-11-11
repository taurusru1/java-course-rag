from education_rag.chunking import ChapterAwareSplitter, CodeAwareSplitter
from processor.import_processor.base import BaseNode
from processor.import_processor.exceptions import StateFieldError
from processor.import_processor.state import ImportGraphState


class NodeDocumentSplit(BaseNode):
    """按照标题层级切分，并补齐教育领域元数据；代码块按 C1 规则整体保留。"""
    name = "node_document_split"

    def __init__(self, *args, splitter: ChapterAwareSplitter | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.splitter = splitter or CodeAwareSplitter(
            max_chars=self.config.max_content_length,
            overlap_chars=min(160, self.config.max_content_length // 5),
        )

    def process(self, state: ImportGraphState) -> ImportGraphState:
        document = state.get("parsed_document")
        if document is None:
            raise StateFieldError(field_name="parsed_document", message="缺少已解析文档")
        chunks = self.splitter.split(document)
        if not chunks:
            raise StateFieldError(field_name="chunks", message="章节切分结果为空")
        state["chunks"] = [chunk.to_record() for chunk in chunks]
        state["chunk_count"] = len(chunks)
        state["import_status"] = "chunked"
        return state
