"""报错案例库与真实 javac 报错的一致性测试。

`backend/src/main/resources/seed/error_cases.json` 同时被两处使用：
- Spring Boot 启动时由 `DataSeeder` 读取，灌入 `error_cases` 表；
- 本测试用它去匹配 `data/errors/javac_errors.json` 里真实采集到的报错文本。

这样「案例正则」不会只对着手写的示例校验，而是对着真实 javac 输出校验——
正则写错、中英文漏写、JDK 升级后文案变化都会在这里失败。
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "backend" / "src" / "main" / "resources" / "seed" / "error_cases.json"
COLLECTED = ROOT / "data" / "errors" / "javac_errors.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def test_error_cases_are_well_formed():
    cases = load(CASES)
    codes = [case["errorCode"] for case in cases]
    assert len(codes) == len(set(codes)), "errorCode 必须唯一"
    for case in cases:
        for field in ("category", "javacPattern", "cause", "solution", "exampleCode"):
            assert case.get(field), f"{case['errorCode']} 缺少字段 {field}"
        # 正则必须能被编译，否则运行时会悄悄退化成关键词匹配
        re.compile(case["javacPattern"])


def test_collected_samples_all_classified():
    data = load(COLLECTED)
    assert data["total"] >= 8
    assert data["unclassified"] == [], f"未归类样例：{data['unclassified']}"
    for item in data["items"]:
        assert item["message"].strip(), f"{item['sample']} 没有采集到报错文本"
        assert item["exit_code"] != 0


def test_patterns_match_real_javac_messages():
    cases = load(CASES)
    data = load(COLLECTED)
    for item in data["items"]:
        message = item["message"]
        hits = [
            case["errorCode"]
            for case in cases
            if re.search(case["javacPattern"], message, re.IGNORECASE | re.DOTALL)
        ]
        assert item["error_code"] in hits, (
            f"{item['sample']} 的真实报错未被案例库覆盖，"
            f"期望 {item['error_code']}，实际命中 {hits}"
        )


def test_runtime_samples_are_covered():
    data = load(COLLECTED)
    kinds = {item["kind"] for item in data["items"]}
    assert kinds == {"compile", "runtime"}, "应同时覆盖编译期与运行期报错"
