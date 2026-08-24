from education_rag.evaluation import demo_dataset, evaluate
from education_rag.models import citation_from_record


def test_all_retrieval_modes_report_required_metrics():
    documents, queries = demo_dataset()
    report = evaluate(documents, queries, top_k=3)
    assert set(report) == {"dense", "hybrid", "hybrid_rerank", "hybrid_rerank_hyde"}
    for metrics in report.values():
        assert {"Recall@3", "MRR", "avg_latency_ms"} <= set(metrics)
        assert 0 <= metrics["Recall@3"] <= 1


def test_knowledge_base_citation_contains_trace_fields():
    citation = citation_from_record({
        "chunk_id": "abc", "course_name": "Python 入门", "project_name": "",
        "chapter_name": "函数", "chapter_path": "Python 入门 > 函数",
        "source_file": "python.md", "page_number": 3,
    })
    assert citation == {
        "source": "knowledge_base", "chunk_id": "abc", "course_name": "Python 入门",
        "project_name": "", "chapter_name": "函数", "chapter_path": "Python 入门 > 函数",
        "source_file": "python.md", "page_number": 3,
    }
