from config.milvus_config import milvus_config
from education_rag.filters import build_milvus_filter
from processor.query_processor.base import NodeBase
from processor.query_processor.state import QueryGraphState
from tool.logger import logger
from utils.embedding_utils import generate_embeddings
from utils.milvus_utils import create_hybrid_search_requests, get_milvus_client, hybrid_search
from utils.task_utils import add_done_task


EDUCATION_OUTPUT_FIELDS = [
    "chunk_id", "content", "content_type", "course_name", "project_name", "chapter_name",
    "chapter_path", "knowledge_points", "question_bank_name", "question_id", "question_type",
    "source_file", "page_number",
]


class NodeSearchEmbedding(NodeBase):
    name = "node_search_embedding"

    def process(self, state: QueryGraphState) -> QueryGraphState:
        try:
            vectors = generate_embeddings([state["rewritten_query"]])
            requests = create_hybrid_search_requests(
                vectors["dense"][0], vectors["sparse"][0],
                expr=build_milvus_filter(state.get("metadata_filters")), limit=10,
            )
            result = hybrid_search(
                get_milvus_client(), milvus_config.chunks_collection, requests,
                ranker_weights=(0.7, 0.3), limit=10, output_fields=EDUCATION_OUTPUT_FIELDS,
            )
            chunks = result[0] if result else []
        except Exception as exc:
            logger.exception(f"教育资料混合检索失败：{exc}")
            chunks = []
        add_done_task(state["session_id"], self.name, state.get("is_stream"))
        return {"embedding_chunks": chunks}
