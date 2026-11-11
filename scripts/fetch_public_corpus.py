#!/usr/bin/env python
"""把公开仓库里适合做课程语料的文件抓到本地（不入库）。

只依赖标准库。默认写到 data/corpus/java/public/<source>/，该目录已 gitignore。

用法:
    python scripts/fetch_public_corpus.py --list
    python scripts/fetch_public_corpus.py --source javaguide
    python scripts/fetch_public_corpus.py --source algorithms --limit 80
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

try:  # Windows 控制台默认 GBK，中文提示会乱码
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "data" / "corpus" / "java" / "public"

SOURCES = {
    "javaguide": {
        "repo": "Snailclimb/JavaGuide",
        "branch": "main",
        "license": "Apache-2.0",
        "kind": "md",
        "prefixes": [
            "docs/java/basis/",
            "docs/java/collection/",
            "docs/java/io/",
            "docs/java/concurrent/",
            "docs/java/jvm/",
        ],
        "note": "Java 基础/集合/IO/并发/JVM 问答体讲义",
        "skip_readme": True,
    },
    "byhieg": {
        "repo": "byhieg/JavaTutorial",
        "branch": "master",
        "license": "MIT",
        "kind": "md",
        "prefixes": ["src/main/java/cn/byhieg/"],
        "note": "多线程/集合/IO/反射/注解 分章教程",
    },
    "algorithms": {
        "repo": "TheAlgorithms/Java",
        "branch": "master",
        "license": "MIT",
        "kind": "java",
        "prefixes": [
            "src/main/java/com/thealgorithms/sorts/",
            "src/main/java/com/thealgorithms/searches/",
            "src/main/java/com/thealgorithms/datastructures/",
            "src/main/java/com/thealgorithms/strings/",
        ],
        "note": "算法与数据结构实现，用于压测代码感知切分",
    },
}

UA = {"User-Agent": "java-course-rag-corpus-fetcher"}


def _token() -> str:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        return token
    try:
        out = subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True, timeout=10
        )
        if out.returncode == 0:
            return out.stdout.strip()
    except Exception:  # noqa: BLE001
        pass
    return ""


_TOKEN = _token()


def _get(url: str, timeout: int = 60) -> bytes:
    headers = dict(UA)
    if _TOKEN:
        headers["Authorization"] = f"Bearer {_TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _get_json(url: str) -> dict:
    return json.loads(_get(url).decode("utf-8"))


def list_files(source: dict, prefixes: list[str] | None = None) -> list[str]:
    repo, branch = source["repo"], source["branch"]
    tree = _get_json(
        f"https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1"
    )
    paths = []
    for item in tree.get("tree", []):
        if item.get("type") != "blob":
            continue
        path = item["path"]
        wanted = prefixes or source["prefixes"]
        if not any(path.startswith(prefix) for prefix in wanted):
            continue
        if source.get("skip_readme") and Path(path).name.lower() == "readme.md":
            continue
        if source["kind"] == "md" and path.endswith(".md"):
            paths.append(path)
        elif source["kind"] == "java" and path.endswith(".java"):
            paths.append(path)
    return sorted(paths)


def raw_url(source: dict, path: str) -> str:
    quoted = urllib.parse.quote(path)
    return f"https://raw.githubusercontent.com/{source['repo']}/{source['branch']}/{quoted}"


def strip_frontmatter(text: str) -> tuple[str, str]:
    """返回 (frontmatter 里的 title, 正文)。没有 frontmatter 时 title 为空。"""
    if not text.startswith("---"):
        return "", text
    end = text.find("\n---", 3)
    if end == -1:
        return "", text
    head = text[3:end]
    title = ""
    for line in head.splitlines():
        if line.strip().startswith("title:"):
            title = line.split(":", 1)[1].strip().strip("\"'")
            break
    return title, text[end + 4 :].lstrip("\n")


def to_markdown(source_name: str, source: dict, path: str, raw: str) -> str:
    header = f"<!-- 来源: https://github.com/{source['repo']}/blob/{source['branch']}/{path} | 许可: {source['license']} -->\n"
    if source["kind"] == "md":
        title, body = strip_frontmatter(raw)
        if not any(line.startswith("# ") for line in body.splitlines()[:5]):
            title = title or Path(path).stem.replace("-", " ")
            body = f"# {title}\n\n{body}"
        return header + "\n" + body
    name = Path(path).stem
    return (
        header
        + f"\n# {name}\n\n"
        + "```java\n"
        + raw.rstrip()
        + "\n```\n"
    )


def fetch(source_name: str, limit: int, out_root: Path, prefixes: list[str] | None = None) -> None:
    source = SOURCES[source_name]
    paths = list_files(source, prefixes)
    if limit:
        paths = paths[:limit]
    written = 0
    total_bytes = 0
    dest_root = out_root / source_name
    print(f"[{source_name}] {source['repo']} -> {dest_root}  ({len(paths)} files)")
    for i, path in enumerate(paths, 1):
        try:
            raw = _get(raw_url(source, path)).decode("utf-8", errors="replace")
        except Exception as exc:  # noqa: BLE001 - 单个文件失败不影响整体
            print(f"  skip {path}: {exc}")
            continue
        rel = Path(path)
        if rel.suffix == ".java":
            rel = rel.with_suffix(".md")
        dest = dest_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        text = to_markdown(source_name, source, path, raw)
        dest.write_text(text, encoding="utf-8", newline="\n")
        written += 1
        total_bytes += len(text.encode("utf-8"))
        if i % 20 == 0:
            print(f"  ... {i}/{len(paths)}")
    print(f"[{source_name}] done: {written} files, {total_bytes/1024:.0f} KB")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=sorted(SOURCES), help="要抓取的源")
    parser.add_argument("--limit", type=int, default=0, help="最多抓取多少个文件（0=全部）")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="输出目录")
    parser.add_argument("--prefix", action="append", default=None, help="只抓取指定前缀（可重复），覆盖数据源默认目录")
    parser.add_argument("--list", action="store_true", help="列出可用数据源")
    args = parser.parse_args()

    if args.list:
        for name, src in SOURCES.items():
            print(f"{name:12s} {src['repo']:32s} {src['license']:12s} {src['note']}")
        return 0
    if not args.source:
        parser.print_help()
        return 1
    fetch(args.source, args.limit, args.out, args.prefix)
    return 0


if __name__ == "__main__":
    sys.exit(main())
