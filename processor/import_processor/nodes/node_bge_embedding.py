from processor.import_processor.base import BaseNode
from processor.import_processor.exceptions import StateFieldError
from processor.import_processor.state import ImportGraphState
from utils.embedding_utils import generate_embeddings


class NodeBGEEmbedding(BaseNode):
    """使用 BGE-M3 生成稠密与稀疏向量。"""
    name = "node_bge_embedding"

    def process(self, state: ImportGraphState) -> ImportGraphState:
        chunks = state.get("chunks") or []
        if not chunks:
            raise StateFieldError(field_name="chunks", message="待向量化切片不能为空")
        for start in range(0, len(chunks), self.config.embedding_batch_size):
            batch = chunks[start:start + self.config.embedding_batch_size]
            vectors = generate_embeddings([self._embedding_text(chunk) for chunk in batch])
            for index, chunk in enumerate(batch):
                chunk["dense_vector"] = vectors["dense"][index]
                chunk["sparse_vector"] = vectors["sparse"][index]
        state.update(chunks=chunks, import_status="embedded")
        return state

    @staticmethod
    def _embedding_text(chunk: dict) -> str:
        metadata = " / ".join(str(value) for value in (
            chunk.get("course_name"), chunk.get("project_name"), chunk.get("chapter_path"),
            "、".join(chunk.get("knowledge_points") or []),
        ) if value)
        return f"{metadata}\n{chunk['content']}" if metadata else chunk["content"]
