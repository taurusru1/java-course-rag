"""扩展语料接入评测：讲义与扩展资料分库检索，各看一组题。

A 组：自建讲义的 21 道题（讲义范围检索，考察接入公开资料后讲义是否仍然好使）
B 组：只有 JavaGuide 能回答的 12 道题（扩展范围检索，考察扩展资料到底有没有用）

用法：
    .venv\\Scripts\\python.exe scripts\\evaluate_public.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from education_rag.embedding import HashingHybridEmbedder  # noqa: E402
from web.offline_service import build_index, retrieve_sections, section_context  # noqa: E402

CORPUS = ROOT / "data" / "corpus" / "java"
TEXTBOOK_EVAL = ROOT / "data" / "eval" / "java_qa.json"
PUBLIC_EVAL = ROOT / "data" / "eval" / "public_qa.json"


def load(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8-sig"))["items"]


def eval_textbook(records: list[dict], items: list[dict]) -> dict:
    recall1 = recall3 = hits = 0
    mrr = 0.0
    failures = []
    for item in items:
        sections = retrieve_sections(records, item["question"], top_k=8, tier="textbook")
        target = item["chapter"]
        position = next((i for i, (_, key, _) in enumerate(sections[:10], start=1) if target in key), None)
        recall1 += 1 if position == 1 else 0
        recall3 += 1 if position and position <= 3 else 0
        mrr += 1 / position if position else 0
        context = section_context(sections[0][2]) if sections else ""
        ok = all(k in context for k in item["keywords"])
        hits += 1 if ok else 0
        if not ok:
            failures.append(item["id"])
    n = len(items)
    return {"r1": recall1 / n, "r3": recall3 / n, "mrr": mrr / n, "kw": hits / n, "failures": failures}


def eval_public(records: list[dict], items: list[dict], drop_code: bool = False) -> dict:
    file_hits = kw_hits = 0
    kw_items = 0
    details = []
    for item in items:
        pool = records
        if drop_code:
            pool = [r for r in records if not r.get("is_code")]
        sections = retrieve_sections(pool, item["question"], top_k=8, tier="extended")
        if not sections:
            details.append({"id": item["id"], "file": "", "ok": False})
            continue
        top_records = sections[0][2]
        files = {record.get("source_file", "") for _, record in top_records}
        hit = any(name in files for name in item["expect_files"])
        file_hits += 1 if hit else 0
        if item["keywords"]:
            kw_items += 1
            context = section_context(top_records)
            kw_hits += 1 if all(k in context for k in item["keywords"]) else 0
        details.append({"id": item["id"], "file": sorted(files)[0] if files else "", "ok": hit})
    n = len(items)
    return {
        "file": file_hits / n,
        "kw": (kw_hits / kw_items) if kw_items else 0.0,
        "details": details,
    }


def main() -> int:
    textbook_items = load(TEXTBOOK_EVAL)
    public_items = load(PUBLIC_EVAL)
    records = build_index(CORPUS, HashingHybridEmbedder())
    extended = [r for r in records if r.get("source_tier") == "extended"]
    print(f"索引片段 {len(records)}（讲义 {len(records) - len(extended)} / 扩展 {len(extended)}）\n")

    a = eval_textbook(records, textbook_items)
    print("A 组（讲义范围检索，21 题）")
    print(f"  Recall@1 {a['r1']:.3f}  Recall@3 {a['r3']:.3f}  MRR {a['mrr']:.3f}  要点命中 {a['kw']:.3f}")
    if a["failures"]:
        print(f"  要点未命中：{', '.join(a['failures'])}")

    b = eval_public(records, public_items)
    b2 = eval_public(records, public_items, drop_code=True)
    print("\nB 组（扩展范围检索，12 题）")
    print(f"  全部扩展资料：文件命中 {b['file']:.3f}  要点命中 {b['kw']:.3f}")
    print(f"  去掉代码片段：文件命中 {b2['file']:.3f}  要点命中 {b2['kw']:.3f}")
    print("  逐题首位来源：")
    for detail in b["details"]:
        print(f"    {detail['id']} {'✓' if detail['ok'] else '✗'} {detail['file']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
