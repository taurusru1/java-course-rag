from typing import Any, TypedDict


class QueryGraphState(TypedDict, total=False):
    session_id: str
    message_id: str
    original_query: str
    rewritten_query: str
    metadata_filters: dict[str, Any]
    history: list[dict]
    embedding_chunks: list
    hyde_embedding_chunks: list
    hyde_doc: str
    web_search_docs: list
    rrf_chunks: list
    reranked_docs: list
    citations: list[dict]
    prompt: str
    answer: str
    is_stream: bool
