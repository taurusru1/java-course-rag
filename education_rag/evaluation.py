from __future__ import annotations

import argparse
import json
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .embedding import HashingHybridEmbedder


@dataclass(slots=True)
class EvalDocument:
    chunk_id: str
    content: str


@dataclass(slots=True)
class EvalQuery:
    query: str
    relevant_chunk_ids: set[str]


class OfflineRetriever:
    """不依赖 Milvus/模型服务的评测实现，用于 CI；算法形态与线上链路一致。"""

    def __init__(self, documents: list[EvalDocument], dimensions: int = 256):
        self.documents = documents
        self.embedder = HashingHybridEmbedder(dimensions)
        vectors = self.embedder.embed_documents([document.content for document in documents])
        self.dense = vectors["dense"]
        self.sparse = vectors["sparse"]

    @staticmethod
    def _dot(left, right) -> float:
        return sum(a * b for a, b in zip(left, right))

    @staticmethod
    def _sparse_dot(left: dict[int, float], right: dict[int, float]) -> float:
        return sum(value * right.get(index, 0.0) for index, value in left.items())

    @staticmethod
    def _normalize(values: list[float]) -> list[float]:
        if not values:
            return []
        low, high = min(values), max(values)
        if math.isclose(low, high):
            return [1.0 if high else 0.0 for _ in values]
        return [(value - low) / (high - low) for value in values]

    def search(self, query: str, mode: str, top_k: int = 3) -> list[str]:
        query_vectors = self.embedder.embed_documents([query])
        dense_scores = [self._dot(query_vectors["dense"][0], vector) for vector in self.dense]
        sparse_scores = [self._sparse_dot(query_vectors["sparse"][0], vector) for vector in self.sparse]
        if mode == "dense":
            scores = dense_scores
        else:
            dense_norm, sparse_norm = self._normalize(dense_scores), self._normalize(sparse_scores)
            scores = [0.7 * dense + 0.3 * sparse for dense, sparse in zip(dense_norm, sparse_norm)]

        ranked = sorted(range(len(scores)), key=lambda index: scores[index], reverse=True)
        if "hyde" in mode:
            hyde_query = f"{query} 教程 知识点 课程章节 题目答案解析 项目步骤"
            hyde_vectors = self.embedder.embed_documents([hyde_query])
            hyde_scores = [self._dot(hyde_vectors["dense"][0], vector) for vector in self.dense]
            hyde_ranked = sorted(range(len(hyde_scores)), key=lambda index: hyde_scores[index], reverse=True)
            rrf: dict[int, float] = {}
            for result_list in (ranked, hyde_ranked):
                for rank, index in enumerate(result_list, start=1):
                    rrf[index] = rrf.get(index, 0.0) + 1.0 / (60 + rank)
            ranked = sorted(rrf, key=rrf.get, reverse=True)

        candidates = ranked[: max(top_k * 3, top_k)]
        if "rerank" in mode:
            query_tokens = set(self.embedder.tokens(query))
            candidates.sort(
                key=lambda index: len(query_tokens & set(self.embedder.tokens(self.documents[index].content))),
                reverse=True,
            )
        return [self.documents[index].chunk_id for index in candidates[:top_k]]


def evaluate(
    documents: list[EvalDocument], queries: list[EvalQuery], top_k: int = 3,
) -> dict[str, dict[str, float]]:
    retriever = OfflineRetriever(documents)
    modes = ("dense", "hybrid", "hybrid_rerank", "hybrid_rerank_hyde")
    report: dict[str, dict[str, float]] = {}
    for mode in modes:
        hits, reciprocal_ranks = 0, []
        start = time.perf_counter()
        for item in queries:
            ranked = retriever.search(item.query, mode, top_k)
            first_rank = next((rank for rank, chunk_id in enumerate(ranked, 1) if chunk_id in item.relevant_chunk_ids), 0)
            hits += int(first_rank > 0)
            reciprocal_ranks.append(1.0 / first_rank if first_rank else 0.0)
        elapsed_ms = (time.perf_counter() - start) * 1000
        count = max(1, len(queries))
        report[mode] = {
            f"Recall@{top_k}": hits / count,
            "MRR": sum(reciprocal_ranks) / count,
            "avg_latency_ms": elapsed_ms / count,
        }
    return report


def demo_dataset() -> tuple[list[EvalDocument], list[EvalQuery]]:
    documents = [
        EvalDocument("python-function", "Python 函数使用 def 定义，参数负责向函数传入数据，并可通过 return 返回结果。"),
        EvalDocument("rag-project", "RAG 项目先解析文档并切分，然后生成向量、混合检索、重排序，最后生成带引用答案。"),
        EvalDocument("question-break", "题型：单选题。循环满足条件后需要提前退出时使用 break。答案：B。"),
        EvalDocument("linux-file", "Linux 可以使用 ls 查看目录文件，使用 cd 切换目录。"),
    ]
    queries = [
        EvalQuery("Python 函数参数有什么作用", {"python-function"}),
        EvalQuery("RAG 项目的检索流程是什么", {"rag-project"}),
        EvalQuery("循环提前退出的选择题答案", {"question-break"}),
    ]
    return documents, queries


def load_jsonl(path: Path) -> tuple[list[EvalDocument], list[EvalQuery]]:
    documents, queries = [], []
    for line in path.read_text(encoding="utf-8").splitlines():
        item = json.loads(line)
        if item["type"] == "document":
            documents.append(EvalDocument(item["chunk_id"], item["content"]))
        elif item["type"] == "query":
            queries.append(EvalQuery(item["query"], set(item["relevant_chunk_ids"])))
    return documents, queries


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="教育 RAG 离线检索评测")
    parser.add_argument("--dataset", type=Path, help="可选 JSONL 评测集")
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args(list(argv) if argv is not None else None)
    documents, queries = load_jsonl(args.dataset) if args.dataset else demo_dataset()
    print(json.dumps(evaluate(documents, queries, args.top_k), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
