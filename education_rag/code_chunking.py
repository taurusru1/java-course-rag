"""代码感知切分（创新点 C1）。

普通按段落切分会把一个 Java 类从中间劈开，检索出来的片段既缺类声明也缺方法头，
向量表示只能捕捉到零散的语句。本模块负责：

1. 把 Markdown 中的围栏代码块识别为原子单元，不与正文混切；
2. 识别代码语言与类 / 方法等结构符号；
3. 超长代码块优先在「类成员边界」处切分，并为每片补上类声明与方法签名上下文。
"""

from __future__ import annotations

import re
from dataclasses import dataclass

FENCE_OPEN = re.compile(r"^[ \t]*(`{3,}|~{3,})[ \t]*([A-Za-z0-9+#._-]*)[ \t]*$")
FENCE_CLOSE = re.compile(r"^[ \t]*(`{3,}|~{3,})[ \t]*$")
TYPE_DECLARATION = re.compile(r"\b(class|interface|enum|record|@interface)\s+([A-Za-z_$][\w$]*)")
METHOD_DECLARATION = re.compile(
    r"(?:^|[;{}])[ \t]*(?:(?:public|private|protected|static|final|abstract|synchronized|native|default)\s+)*"
    r"[\w<>\[\],.?\s]+?\s+([A-Za-z_$][\w$]*)\s*\([^;{}]*\)\s*(?:throws[^{]+)?\{",
    re.MULTILINE,
)
PYTHON_DEF = re.compile(r"^[ \t]*(?:async\s+)?(?:def|class)\s+([A-Za-z_]\w*)", re.MULTILINE)

LANGUAGE_ALIASES = {
    "java": "java",
    "py": "python",
    "python": "python",
    "js": "javascript",
    "javascript": "javascript",
    "ts": "typescript",
    "typescript": "typescript",
    "sql": "sql",
    "xml": "xml",
    "html": "xml",
    "sh": "shell",
    "bash": "shell",
    "shell": "shell",
    "json": "json",
    "yaml": "yaml",
    "yml": "yaml",
}


@dataclass(slots=True)
class CodeBlock:
    language: str
    code: str


def parse_markdown_units(text: str) -> list[tuple[str, str | CodeBlock]]:
    """把 Markdown 文本拆成有序的正文 / 代码块单元，代码块保持完整。"""
    lines = text.split("\n")
    units: list[tuple[str, str | CodeBlock]] = []
    prose: list[str] = []
    index = 0
    while index < len(lines):
        opening = FENCE_OPEN.match(lines[index])
        if not opening:
            prose.append(lines[index])
            index += 1
            continue
        fence_chars = opening.group(1)
        marker, length = fence_chars[0], len(fence_chars)
        cursor = index + 1
        body: list[str] = []
        while cursor < len(lines):
            closing = FENCE_CLOSE.match(lines[cursor])
            if closing and closing.group(1)[0] == marker and len(closing.group(1)) >= length:
                break
            body.append(lines[cursor])
            cursor += 1
        if prose:
            merged = "\n".join(prose).strip()
            if merged:
                units.append(("text", merged))
            prose = []
        units.append(("code", CodeBlock(language=opening.group(2).lower(), code="\n".join(body))))
        index = cursor + 1
    if prose:
        merged = "\n".join(prose).strip()
        if merged:
            units.append(("text", merged))
    return units


def detect_language(code: str, fence_language: str = "") -> str:
    """围栏标注优先；没有标注时按代码特征猜测，猜不出返回 text。"""
    if fence_language:
        return LANGUAGE_ALIASES.get(fence_language, fence_language)
    if re.search(r"\b(?:public|private|protected)\s+(?:static\s+)?(?:final\s+)?(?:class|interface|enum|record|void)\b", code):
        return "java"
    if "System.out.print" in code or re.search(r"\bpublic\s+static\s+void\s+main\b", code):
        return "java"
    if re.search(r"^\s*(?:async\s+)?def\s+\w+\s*\(", code, re.MULTILINE) or re.search(r"^\s*import\s+\w+\s*$", code, re.MULTILINE):
        return "python"
    if re.search(r"\b(?:function|const|let)\s+\w+\s*[=(]", code) or "=>" in code:
        return "javascript"
    if re.search(r"\bSELECT\b.+\bFROM\b", code, re.IGNORECASE | re.DOTALL):
        return "sql"
    return "text"


def extract_symbols(code: str, language: str = "", limit: int = 8) -> list[str]:
    """提取类名 / 方法名，作为代码片段的结构标签。"""
    symbols: list[str] = []

    def add(name: str) -> None:
        if name and name not in symbols:
            symbols.append(name)

    for match in TYPE_DECLARATION.finditer(code):
        add(match.group(2))
    if language == "python":
        for match in PYTHON_DEF.finditer(code):
            add(match.group(1))
    else:
        for match in METHOD_DECLARATION.finditer(code):
            add(match.group(1))
    return symbols[:limit]


def _line_depths(lines: list[str]) -> list[int]:
    """逐行统计花括号深度，跳过字符串、字符与注释中的括号。"""
    depths: list[int] = []
    depth = 0
    in_block_comment = False
    for line in lines:
        index = 0
        while index < len(line):
            char = line[index]
            nxt = line[index + 1] if index + 1 < len(line) else ""
            if in_block_comment:
                if char == "*" and nxt == "/":
                    in_block_comment = False
                    index += 2
                    continue
                index += 1
                continue
            if char == "/" and nxt == "/":
                break
            if char == "/" and nxt == "*":
                in_block_comment = True
                index += 2
                continue
            if char in {'"', "'"}:
                quote = char
                index += 1
                while index < len(line):
                    if line[index] == "\\":
                        index += 2
                        continue
                    if line[index] == quote:
                        index += 1
                        break
                    index += 1
                continue
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
            index += 1
        depths.append(depth)
    return depths


def _split_by_lines(code: str, max_chars: int, overlap_chars: int) -> list[str]:
    lines = code.split("\n")
    pieces: list[str] = []
    current: list[str] = []
    size = 0
    for line in lines:
        extra = len(line) + 1
        if current and size + extra > max_chars:
            pieces.append("\n".join(current))
            overlap: list[str] = []
            overlap_size = 0
            for previous in reversed(current):
                if overlap_size + len(previous) + 1 > overlap_chars:
                    break
                overlap.insert(0, previous)
                overlap_size += len(previous) + 1
            current = overlap
            size = overlap_size
        current.append(line)
        size += extra
    if current:
        pieces.append("\n".join(current))
    return [piece for piece in pieces if piece.strip()]


def split_java_code(code: str, max_chars: int, overlap_chars: int = 0) -> list[str]:
    """在类成员边界切分 Java 代码：每个片段都带上类声明，便于单独成块检索。"""
    if len(code) <= max_chars:
        return [code]
    lines = code.split("\n")
    depths = _line_depths(lines)
    body_start = next((i for i, depth in enumerate(depths) if depth >= 1), None)
    if body_start is None:
        return _split_by_lines(code, max_chars, overlap_chars)

    header = lines[: body_start + 1]
    cuts = [
        i
        for i in range(body_start + 1, len(lines))
        if depths[i] == 1 and lines[i].strip().endswith("}")
    ]
    groups: list[list[str]] = []
    start = body_start + 1
    for cut in cuts:
        groups.append(lines[start : cut + 1])
        start = cut + 1
    if start < len(lines):
        groups.append(lines[start:])

    header_text = "\n".join(header)
    budget = max_chars - len(header_text) - 8
    if budget < 200:
        return _split_by_lines(code, max_chars, overlap_chars)

    pieces: list[str] = []
    current: list[str] = []
    size = 0
    for group in groups:
        group_text = "\n".join(group)
        if len(group_text) > budget:
            if current:
                pieces.append("\n".join(current))
                current, size = [], 0
            for sub in _split_by_lines(group_text, budget, overlap_chars):
                pieces.append(f"{header_text}\n{sub}")
            continue
        if current and size + len(group_text) + 1 > budget:
            pieces.append("\n".join(current))
            current, size = [], 0
        current.extend(group)
        size += len(group_text) + 1
    if current:
        pieces.append("\n".join(current))

    header_stripped = header_text.lstrip()
    result: list[str] = []
    for piece in pieces:
        result.append(piece if piece.lstrip().startswith(header_stripped) else f"{header_text}\n{piece}")
    return result or [code]
