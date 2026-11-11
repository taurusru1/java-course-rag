"""对比「章节切分」与「代码感知切分」在同一份讲义上的切片质量。

用法：python scripts/compare_chunking.py [讲义路径] [--max-chars 600]

指标说明：
- 片段数 / 平均长度 / 最长片段；
- 围栏完整率：代码块没有被切碎的片段占比（奇数个 ``` 说明围栏被切断）；
- 类声明保留率：代码片段中仍能看到 class 声明的比例（决定检索时能否理解上下文）。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from education_rag.chunking import ChapterAwareSplitter, CodeAwareSplitter
from education_rag.parsing import EducationDocumentParser


def _metrics(name: str, chunks: list) -> dict:
    lengths = [len(chunk.content) for chunk in chunks]
    broken = [chunk for chunk in chunks if chunk.content.count("```") % 2 == 1]
    code_chunks = [chunk for chunk in chunks if chunk.content.count("```") >= 2]
    with_class = [chunk for chunk in code_chunks if "class " in chunk.content]
    return {
        "策略": name,
        "片段数": len(chunks),
        "平均长度": round(sum(lengths) / len(lengths)) if lengths else 0,
        "最长片段": max(lengths) if lengths else 0,
        "围栏完整率": f"{(1 - len(broken) / len(chunks)) * 100:.0f}%" if chunks else "-",
        "切断代码的片段": len(broken),
        "含类声明的代码片段": f"{len(with_class)}/{len(code_chunks)}",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default="data/corpus/java/ch01-basics.md")
    parser.add_argument("--max-chars", type=int, default=600)
    args = parser.parse_args()

    document = EducationDocumentParser().parse(args.path)
    baseline = ChapterAwareSplitter(max_chars=args.max_chars, overlap_chars=60).split(document)
    code_aware = CodeAwareSplitter(max_chars=args.max_chars, overlap_chars=60).split(document)

    rows = [_metrics("章节切分（基线）", baseline), _metrics("代码感知切分（C1）", code_aware)]
    headers = list(rows[0].keys())
    widths = [max(len(str(row[key])) for row in rows + [dict(zip(headers, headers))]) for key in headers]

    print(f"讲义：{args.path}（max_chars={args.max_chars}）\n")
    print("| " + " | ".join(str(h).ljust(w) for h, w in zip(headers, widths)) + " |")
    print("|" + "|".join("-" * (w + 2) for w in widths) + "|")
    for row in rows:
        print("| " + " | ".join(str(row[key]).ljust(w) for key, w in zip(headers, widths)) + " |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
