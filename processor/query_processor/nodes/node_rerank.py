from typing import Any

from processor.query_processor.base import NodeBase
from processor.query_processor.state import QueryGraphState
from tool.logger import logger
from utils.reranker_http_utils import rerank_documents
from utils.task_utils import add_done_task


class NodeRerank(NodeBase):
    """Cross-Encoder 精排；服务不可用时保留 RRF 顺序。"""
    name = "node_rerank"
    max_top_k = 5

    def process(self, state: QueryGraphState) -> QueryGraphState:
        documents = self._merge_sources(state)
        if documents:
            try:
                scores = rerank_documents(state["rewritten_query"], [doc["content"] for doc in documents])
                documents = sorted(
                    ({**doc, "score": float(score)} for doc, score in zip(documents, scores)),
                    key=lambda item: item["score"], reverse=True,
                )
            except Exception as exc:
                logger.warning(f"Reranker 不可用，使用 RRF/搜索原顺序：{exc}")
                documents = [{**doc, "score": 0.0} for doc in documents]
        state["reranked_docs"] = documents[:self.max_top_k]
        add_done_task(state["session_id"], self.name, state.get("is_stream"))
        return state

    @staticmethod
    def _merge_sources(state: QueryGraphState) -> list[dict[str, Any]]:
        documents = []
        for record in state.get("rrf_chunks") or []:
            documents.append({**record, "source": "knowledge_base", "url": ""})
        for record in state.get("web_search_docs") or []:
            documents.append({
                "chunk_id": "", "content": record.get("snippet", ""), "source": "web",
                "title": record.get("title", ""), "url": record.get("url", ""),
            })
        return [doc for doc in documents if doc.get("content")]
