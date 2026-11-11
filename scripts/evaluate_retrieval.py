"""检索评测：对比「纯向量」与「向量 + 词面」两种打分的召回效果。

用法：
    .venv\\Scripts\\python.exe scripts\\evaluate_retrieval.py
    .venv\\Scripts\\python.exe scripts\\evaluate_retrieval.py --json docs/评测结果.json

指标：
    Recall@1  第一名就是目标章节的比例
    Recall@3  前三名包含目标章节的比例
    MRR       目标章节在排名中位置的倒数的平均值
    要点命中率 第一名的内容包含该题全部关键要点的比例（近似的答案正确性）
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from education_rag.embedding import HashingHybridEmbedder  # noqa: E402
from web.offline_service import build_index, cosine, rank_hybrid  # noqa: E402

EVAL_PATH = ROOT / "data" / "eval" / "java_qa.json"
CORPUS = ROOT / "data" / "corpus" / "java"


def score_vector(query: str, records: list[dict], embedder: HashingHybridEmbedder) -> list[tuple[float, dict]]:
    query_vector = embedder.embed_documents([query])["dense"][0]
    return sorted(
        ((cosine(query_vector, record.get("dense_vector") or []), record) for record in records),
        key=lambda item: item[0],
        reverse=True,
    )


def score_hybrid(query: str, records: list[dict], embedder: HashingHybridEmbedder) -> list[tuple[float, dict]]:
    """与在线服务完全一致的混合排序。"""
    return rank_hybrid(records, query, len(records))


def score_lexical(query: str, records: list[dict], embedder: HashingHybridEmbedder) -> list[tuple[float, dict]]:
    """消融对照：只按词面重合率排序，相当于最朴素的词袋检索。"""
    query_tokens = set(embedder.tokens(query))
    scored = []
    for record in records:
        text_tokens = set(embedder.tokens(record.get("content", "")))
        overlap = len(query_tokens & text_tokens) / len(query_tokens) if query_tokens else 0.0
        scored.append((overlap, record))
    return sorted(scored, key=lambda item: item[0], reverse=True)


def evaluate(items: list[dict], records: list[dict], scorer) -> dict:
    embedder = HashingHybridEmbedder()
    recall1 = recall3 = 0
    mrr = 0.0
    keyword_hits = 0
    details = []
    for item in items:
        ranked = scorer(item["question"], records, embedder)
        target = item["chapter"]
        position = next(
            (index for index, (_, record) in enumerate(ranked[:10], start=1) if target in record.get("chapter_path", "")),
            None,
        )
        recall1 += 1 if position == 1 else 0
        recall3 += 1 if position and position <= 3 else 0
        mrr += 1 / position if position else 0
        top_content = ranked[0][1].get("content", "") if ranked else ""
        hit = all(keyword in top_content for keyword in item["keywords"])
        keyword_hits += 1 if hit else 0
        details.append({"id": item["id"], "rank": position, "keywords_hit": hit})
    total = len(items)
    return {
        "total": total,
        "recall@1": round(recall1 / total, 4),
        "recall@3": round(recall3 / total, 4),
        "mrr": round(mrr / total, 4),
        "keyword_hit": round(keyword_hits / total, 4),
        "details": details,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path, help="把完整结果写入 JSON 文件")
    args = parser.parse_args()

    payload = json.loads(EVAL_PATH.read_text(encoding="utf-8-sig"))
    items = payload["items"]
    records = build_index(CORPUS, HashingHybridEmbedder())
    print(f"语料片段数：{len(records)}；评测题数：{len(items)}\n")

    results = {
        "vector": evaluate(items, records, score_vector),
        "lexical": evaluate(items, records, score_lexical),
        "hybrid": evaluate(items, records, score_hybrid),
    }
    header = f"{'策略':<20}{'Recall@1':>10}{'Recall@3':>10}{'MRR':>10}{'要点命中率':>12}"
    print(header)
    print("-" * len(header))
    for name, label in (
        ("vector", "纯向量"),
        ("lexical", "纯词面"),
        ("hybrid", "向量+词面（混合）"),
    ):
        row = results[name]
        print(f"{label:<20}{row['recall@1']:>10.3f}{row['recall@3']:>10.3f}{row['mrr']:>10.3f}{row['keyword_hit']:>12.3f}")

    failures = [detail for detail in results["hybrid"]["details"] if not detail["keywords_hit"]]
    if failures:
        print(f"\n要点未命中：{', '.join(item['id'] for item in failures)}")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps({"corpus_size": len(records), **results}, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n已写入 {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
