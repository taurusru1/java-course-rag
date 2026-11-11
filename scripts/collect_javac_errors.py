"""采集真实 javac / JVM 报错文本，作为报错诊断知识库（C2）的原始语料与回归用例。

做法：
1. 把 `data/errors/samples/*.java` 复制到临时目录（javac 要求文件名与 public 类名一致）；
2. 逐个子进程调用 `javac -encoding UTF-8`，捕获 stderr；
3. 编译通过的样例（运行时异常）再用 `java` 执行，捕获异常首行；
4. 按关键词把报错归类到 `error_code`，写入 `data/errors/javac_errors.json`。

为什么要单独写采集脚本：javac 的报错文本随 JDK 版本与**系统语言**变化（中文 Windows 输出
"错误: 找不到符号"，英文环境输出 "error: cannot find symbol"），而 javac 输出的字符编码
跟随平台默认编码（本机为 GBK）。这里按 `locale.getpreferredencoding()` 解码并在失败时回退，
避免把乱码当成报错内容入库。

用法：
    .venv\\Scripts\\python.exe scripts\\collect_javac_errors.py
"""

from __future__ import annotations

import json
import locale
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "data" / "errors" / "samples"
OUTPUT = ROOT / "data" / "errors" / "javac_errors.json"

JAVAC = os.environ.get("JAVAC") or shutil.which("javac") or r"D:\Develop\JDK\jdk-17\bin\javac.exe"
JAVA = os.environ.get("JAVA") or shutil.which("java") or r"D:\Develop\JDK\jdk-17\bin\java.exe"

# 关键词 → error_code，覆盖中英文两种 javac 输出
RULES = [
    ("cannot_find_symbol", ("找不到符号", "cannot find symbol")),
    ("incompatible_types", ("不兼容的类型", "incompatible types")),
    ("missing_return_statement", ("缺少返回语句", "missing return statement")),
    ("duplicate_variable", ("定义了变量", "already defined")),
    ("missing_semicolon", ("需要';'", "';' expected", "expected ';'")),
    ("non_static_context", ("无法从静态上下文", "non-static")),
    ("null_pointer", ("NullPointerException",)),
    ("array_index_out_of_bounds", ("ArrayIndexOutOfBoundsException", "IndexOutOfBoundsException")),
]


def decode(data: bytes) -> str:
    """javac 的输出编码跟随平台默认编码，Linux CI 上通常是 UTF-8。"""
    for encoding in (locale.getpreferredencoding(False), "gbk", "utf-8"):
        try:
            return data.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    return data.decode("utf-8", errors="replace")


def classify(message: str) -> str | None:
    for code, keywords in RULES:
        if any(keyword in message for keyword in keywords):
            return code
    return None


def first_error_line(message: str) -> str:
    for line in message.splitlines():
        if "错误" in line or "error" in line.lower():
            return line.strip()
    return message.strip().splitlines()[0] if message.strip() else ""


def collect() -> list[dict]:
    items: list[dict] = []
    with tempfile.TemporaryDirectory() as tmp:
        build = Path(tmp) / "classes"
        build.mkdir()
        for sample in sorted(SAMPLES.glob("*.java")):
            work = Path(tmp) / "src"
            work.mkdir(exist_ok=True)
            copy = work / sample.name
            shutil.copyfile(sample, copy)
            compiled = subprocess.run(
                [JAVAC, "-encoding", "UTF-8", "-d", str(build), str(copy)],
                capture_output=True,
            )
            message = decode(compiled.stderr or compiled.stdout).strip()
            kind = "compile"
            if compiled.returncode == 0:
                kind = "runtime"
                run = subprocess.run(
                    [JAVA, "-Dfile.encoding=UTF-8", "-cp", str(build), sample.stem],
                    capture_output=True,
                )
                message = decode(run.stderr or run.stdout).strip()
            items.append(
                {
                    "sample": sample.stem,
                    "kind": kind,
                    "exit_code": compiled.returncode if kind == "compile" else 1,
                    "error_code": classify(message),
                    "first_line": first_error_line(message),
                    "message": message,
                }
            )
    return items


def main() -> int:
    if not SAMPLES.exists():
        print(f"样例目录不存在：{SAMPLES}", file=sys.stderr)
        return 1
    items = collect()
    unknown = [item["sample"] for item in items if item["error_code"] is None]
    payload = {
        "collected_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "javac": decode(subprocess.run([JAVAC, "-version"], capture_output=True).stdout).strip(),
        "total": len(items),
        "unclassified": unknown,
        "items": items,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"采集 {len(items)} 条，写入 {OUTPUT}")
    for item in items:
        print(f"  {item['sample']:<22} {item['kind']:<8} {item['error_code'] or '?'}")
    if unknown:
        print(f"未归类样例：{', '.join(unknown)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
