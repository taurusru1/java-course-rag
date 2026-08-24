from config.milvus_config import milvus_config
from education_rag.filters import build_milvus_filter
from processor.query_processor.base import NodeBase
from processor.query_processor.nodes.node_search_embedding import EDUCATION_OUTPUT_FIELDS
from processor.query_processor.prompt.search_embedding_hyde import HYDE_PROMPT
from processor.query_processor.state import QueryGraphState
from tool.logger import logger
from utils.embedding_utils import generate_embeddings
from utils.llm_utils import get_llm_client
from utils.milvus_utils import create_hybrid_search_requests, get_milvus_client, hybrid_search
from utils.task_utils import add_done_task


class NodeSearchEmbeddingHyde(NodeBase):
    name = "node_search_embedding_hyde"

    def process(self, state: QueryGraphState) -> QueryGraphState:
        query = state["rewritten_query"]
        try:
            prompt = HYDE_PROMPT.format(rewritten_query=query)
            hyde_doc = get_llm_client().invoke(prompt).content
            vectors = generate_embeddings([f"{query}\n{hyde_doc}"])
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
            logger.warning(f"HyDE 不可用，本轮仅使用普通混合检索：{exc}")
            hyde_doc, chunks = "", []
        add_done_task(state["session_id"], self.name, state.get("is_stream"))
        return {"hyde_embedding_chunks": chunks, "hyde_doc": hyde_doc}
