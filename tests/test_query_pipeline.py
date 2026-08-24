from processor.query_processor.main_graph import KBQueryWorkflow
from processor.query_processor.nodes.node_answer_output import NodeAnswerOutput
from processor.query_processor.nodes.node_query_understanding import NodeQueryUnderstanding
from processor.query_processor.nodes.node_search_embedding import NodeSearchEmbedding
from processor.query_processor.nodes.node_search_embedding_hyde import NodeSearchEmbeddingHyde
from processor.query_processor.nodes.node_web_search_mcp import NodeWebSearchMcp


def test_query_graph_retrieval_rerank_and_cited_answer(monkeypatch):
    record = {
        "chunk_id": "python-function-1",
        "content": "Python 函数使用 def 定义，参数用于传入数据。",
        "content_type": "course_document",
        "course_name": "Python 入门",
        "project_name": "",
        "chapter_name": "函数",
        "chapter_path": "Python 入门 > 函数",
        "knowledge_points": ["函数"],
        "question_bank_name": "",
        "question_id": "",
        "question_type": "",
        "source_file": "Python课程.md",
        "page_number": 0,
    }

    def understand(self, state):
        state.update(rewritten_query=state["original_query"], metadata_filters={}, history=[])
        return state

    monkeypatch.setattr(NodeQueryUnderstanding, "process", understand)
    monkeypatch.setattr(NodeSearchEmbedding, "process", lambda self, state: {"embedding_chunks": [{"entity": record}]})
    monkeypatch.setattr(NodeSearchEmbeddingHyde, "process", lambda self, state: {"hyde_embedding_chunks": []})
    monkeypatch.setattr(NodeWebSearchMcp, "process", lambda self, state: {"web_search_docs": []})
    monkeypatch.setattr(
        "processor.query_processor.nodes.node_rerank.rerank_documents",
        lambda query, documents: [0.99 for _ in documents],
    )

    def generate(state, prompt):
        state["answer"] = "Python 使用 def 定义函数，参数负责传入数据。[1]"

    monkeypatch.setattr(NodeAnswerOutput, "_generate", staticmethod(generate))
    monkeypatch.setattr(NodeAnswerOutput, "_save_history", staticmethod(lambda state: None))

    result = KBQueryWorkflow().run({
        "session_id": "test-session", "original_query": "Python 函数参数有什么作用？", "is_stream": False,
    })
    assert result["answer"].endswith("[1]")
    assert result["reranked_docs"][0]["score"] == 0.99
    assert result["citations"][0]["source"] == "knowledge_base"
    assert result["citations"][0]["chunk_id"] == "python-function-1"
