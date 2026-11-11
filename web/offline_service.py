"""离线降级 AI 服务。

在没有 LLM API Key、没有 Milvus/BGE-M3 的机器上，仍然可以跑通
「Vue → Spring Boot → Python」三端问答链路：检索使用纯 Python 的
确定性哈希向量（HashingHybridEmbedder），回答由检索片段抽取生成，
不调用任何外部网络。

启动：
    .venv\\Scripts\\python.exe -m uvicorn web.offline_service:app --port 9000

它与 web/api 下真实服务的接口契约一致（/ai/query/start 等），
因此 Spring Boot 端无需改动即可在两者之间切换。
"""

from __future__ import annotations

import json
import math
import os
import re
import threading
import time
import uuid
from collections import Counter
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import StreamingResponse

from education_rag.chunking import CodeAwareSplitter
from education_rag.embedding import HashingHybridEmbedder
from education_rag.parsing import EducationDocumentParser

DEFAULT_CORPUS = Path(__file__).resolve().parent.parent / "data" / "corpus" / "java"
MIN_SCORE = 0.05
SENTENCE_STOPS = "。！？；!?;"
# 中文虚词与疑问词：它们几乎出现在每段讲义里，留着只会稀释真正的术语。
STOPWORDS = frozenset("的了是吗呢啊吧呀什么怎样为意思请问我你它他她和与有个这那就都也不很")
_CONTEXT_LINE = re.compile(r"^【[^】]{0,24}】.*$", re.MULTILINE)
_CONTEXT_LINE_PART = re.compile(r"（片段 \d+/\d+）")


def build_index(corpus_dir: Path, embedder: HashingHybridEmbedder) -> list[dict[str, Any]]:
    """解析语料目录，返回带向量与元数据的片段列表。"""
    parser = EducationDocumentParser()
    splitter = CodeAwareSplitter()
    records: list[dict[str, Any]] = []
    if not corpus_dir.exists():
        return records
    for path in sorted(corpus_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in parser.supported_extensions:
            continue
        document = parser.parse(path)
        chunks = splitter.split(document)
        if not chunks:
            continue
        vectors = embedder.embed_documents([chunk.embedding_text() for chunk in chunks])
        for position, chunk in enumerate(chunks):
            record = chunk.to_record()
            record["dense_vector"] = vectors["dense"][position]
            records.append(record)
    return records


def cosine(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    norm = math.sqrt(sum(a * a for a in left)) * math.sqrt(sum(b * b for b in right))
    return dot / norm if norm else 0.0


def search(records: list[dict[str, Any]], query: str, top_k: int = 3) -> list[tuple[float, dict[str, Any]]]:
    """按混合打分召回，返回 [(score, record)]，已按分数降序。"""
    if not records or not query.strip():
        return []
    return rank_hybrid(records, query, top_k)


def rank_hybrid(records: list[dict[str, Any]], query: str, top_k: int = 3) -> list[tuple[float, dict[str, Any]]]:
    """对外的混合排序入口，评测脚本与在线服务共用同一实现。"""
    return _rank(records, query, top_k)


def _overlap_score(query_tokens: set[str], text_tokens: list[str]) -> float:
    """词面重合：按查询词的词频加权，而不是只看「出现过没有」。

    「多态是什么意思」早期被排到 2.5 节的直接原因不是词频，而是「是/什/么/意/思」
    这些虚词把重合率的分母撑大、把真正的术语稀释掉；因此先过滤停用词（见
    `content_tokens`），再对命中词按 `log(1+tf)` 求和——反复讲解该术语的小节胜出，
    且与文档长度无关。
    """
    if not query_tokens:
        return 0.0
    counts = Counter(text_tokens)
    total = sum(math.log1p(counts[token]) for token in query_tokens)
    return min(1.0, total / len(query_tokens))


def content_tokens(text: str, embedder: HashingHybridEmbedder) -> list[str]:
    """去掉中文虚词后的检索词，用于词面打分（向量仍用原始 token）。"""
    return [token for token in embedder.tokens(text) if token not in STOPWORDS]


def lexical_score(query: str, text: str, embedder: HashingHybridEmbedder | None = None) -> float:
    """词面相关度：0.8 × 集合重合 + 0.2 × 词频重合。"""
    embedder = embedder or HashingHybridEmbedder()
    query_tokens = set(content_tokens(query, embedder))
    text_tokens = content_tokens(text, embedder)
    if not query_tokens:
        return 0.0
    coverage = len(query_tokens & set(text_tokens)) / len(query_tokens)
    return 0.8 * coverage + 0.2 * _overlap_score(query_tokens, text_tokens)


def _rank(records: list[dict[str, Any]], query: str, top_k: int) -> list[tuple[float, dict[str, Any]]]:
    """混合打分：0.5 × 向量余弦 + 0.5 × 词面相关度。

    纯哈希向量在中文上区分度有限，加一路词面信号可以让「问什么就排什么」
    更稳定，这也是评测里「混合检索」的最简基线。
    （曾试过对代码片段降权 0.05–0.3，21 题标注集上指标完全不变，故未采用。）
    """
    embedder = HashingHybridEmbedder()
    query_vector = embedder.embed_documents([query])["dense"][0]
    scored = []
    for record in records:
        semantic = cosine(query_vector, record.get("dense_vector") or [])
        lexical = lexical_score(query, record.get("content", ""), embedder)
        scored.append((0.5 * semantic + 0.5 * lexical, record))
    scored.sort(key=lambda item: item[0], reverse=True)
    return scored[:top_k]


def _section_key(record: dict[str, Any]) -> str:
    return record.get("chapter_path") or record.get("chapter_name") or record.get("source_file", "")


def group_by_section(hits: list[tuple[float, dict[str, Any]]]) -> dict[str, list[tuple[float, dict[str, Any]]]]:
    """按小节聚合候选片段：同一个 `chapter_path` 属于同一节。"""
    sections: dict[str, list[tuple[float, dict[str, Any]]]] = {}
    for score, record in hits:
        sections.setdefault(_section_key(record), []).append((score, record))
    return sections


def rerank_sections(
    hits: list[tuple[float, dict[str, Any]]],
    bonus: float = 0.03,
    cap: float = 0.12,
):
    """小节级重排：小节分 = 最高片段分 + 证据密度奖励。

    动机（见 docs/评测方法.md 第 5 节）：失败案例是「同一小节的相邻片段互相挤占第一名」，
    片段级打分看不到「这一节有两三片都在响应这个问题」这一信号。把同一节的多个片段
    聚合后再比较，相当于用「证据密度」给小节加权，且不会把答案拆散。

    （另试过「覆盖增益」：查询词被同节其它片段补齐就再加权 0.10，21 题上指标一字未变，
    故未采用——同 q02/q20 的失败原因不是覆盖不足，而是同义表述的字面碰撞。）
    """
    ranked = []
    for key, items in group_by_section(hits).items():
        items.sort(key=lambda item: item[0], reverse=True)
        score = items[0][0] + min(cap, bonus * (len(items) - 1))
        ranked.append((score, key, items))
    ranked.sort(key=lambda item: item[0], reverse=True)
    return ranked


def strip_context(text: str) -> str:
    """去掉代码片段前置的【Java 代码】课程｜章节｜结构：… 元数据行。

    这行是切分时为向量表示补的章节语义（见 docs/代码感知切分.md），
    对模型有用，但不该出现在给学生的答案里。
    """
    cleaned = _CONTEXT_LINE.sub("", text)
    return _CONTEXT_LINE_PART.sub("", cleaned).strip()


def section_chunks(items: list[tuple[float, dict[str, Any]]], max_chunks: int = 3) -> list[dict[str, Any]]:
    """取小节内若干片段：正文优先、代码靠后，按片段序号还原阅读顺序。"""
    ordered = sorted(items, key=lambda item: item[1].get("part", 0))
    prose = [record for _, record in ordered if not record.get("is_code")]
    code = [record for _, record in ordered if record.get("is_code")]
    chosen = (prose + code)[:max_chunks]
    chosen.sort(key=lambda record: record.get("part", 0))
    return [record for record in chosen if record.get("content")]


def section_context(items: list[tuple[float, dict[str, Any]]], max_chunks: int = 3) -> str:
    """小节上下文：把该节命中的片段拼成一段可读的讲义摘录。"""
    return "\n\n".join(strip_context(record["content"]) for record in section_chunks(items, max_chunks))


def retrieve_sections(records: list[dict[str, Any]], query: str, top_k: int = 8) -> list[tuple[float, str, list]]:
    """混合召回候选片段 -> 小节聚合 -> 小节级重排。"""
    if not records or not query.strip():
        return []
    return rerank_sections(rank_hybrid(records, query, top_k))


def _first_sentences(text: str, limit: int = 3, max_chars: int = 300) -> str:
    """取片段开头的若干句，用于抽取式回答。"""
    cleaned = " ".join(line.strip() for line in strip_context(text).splitlines() if line.strip())
    if "```" in cleaned:
        cleaned = cleaned.split("```", 1)[0].strip()
    sentences: list[str] = []
    buffer = ""
    for char in cleaned:
        buffer += char
        if char in SENTENCE_STOPS and len(buffer.strip()) > 1:
            sentences.append(buffer.strip())
            buffer = ""
            if len(sentences) >= limit:
                break
    if buffer.strip() and len(sentences) < limit:
        sentences.append(buffer.strip())
    answer = "".join(sentences)
    answer = answer[:max_chars].strip().rstrip("；;，,")
    if answer and answer[-1] not in "。！？!?.":
        answer += "。"
    return answer


def cite(record: dict[str, Any]) -> dict[str, Any]:
    """生成与真实服务一致结构的引用。"""
    return {
        "source": "knowledge_base",
        "chunk_id": record.get("chunk_id", ""),
        "course_name": record.get("course_name", ""),
        "project_name": record.get("project_name", ""),
        "chapter_name": record.get("chapter_name", ""),
        "chapter_path": record.get("chapter_path", ""),
        "source_file": record.get("source_file", ""),
        "page_number": record.get("page_number", 0),
    }


def _is_related_snippet(text: str, query: str) -> bool:
    """补充说明的来源是否与问题「真的相关」：要求命中至少 2 个查询词。

    只按分数比例判断会把无关小节带进来——分数整体偏低时，0.8×best 仍然能圈进
    只是共享「什么」「方法」这类高频词的段落。计数器/类型名（`try`、`int`、`double`）
    是可验证的锚点，因此只要问句里有英文标识符，就优先按它们判定。
    """
    embedder = HashingHybridEmbedder()
    query_tokens = set(embedder.tokens(query))
    text_tokens = set(embedder.tokens(text))
    identifiers = {token for token in query_tokens if len(token) >= 2 and token.isascii()}
    if identifiers:
        return len(identifiers & text_tokens) >= 2
    shared = query_tokens & text_tokens
    return len(shared) >= 3


def missing_identifiers(query: str, context: str) -> list[str]:
    """问句里出现、但检索上下文完全没有的英文标识符。

    用于诚实性提示：学生问「HashMap 和 Hashtable 的区别」时讲义只讲了 HashMap，
    如果不说明，答案看起来像是回答了两个概念。只统计长度 ≥3 的 ASCII 词，
    避免把 `try`、`int` 这类极短的语法关键字误报成缺漏。
    """
    embedder = HashingHybridEmbedder()
    wanted = {token for token in embedder.tokens(query) if len(token) >= 3 and token.isascii()}
    have = set(embedder.tokens(context))
    return sorted(wanted - have)


def compose_section_answer(query: str, sections: list[tuple[float, str, list]]) -> tuple[str, list[dict[str, Any]]]:
    """基于小节上下文生成抽取式回答：主答案来自最相关小节的多片拼接。"""
    if not sections or sections[0][0] < MIN_SCORE:
        return (
            "当前知识库中没有检索到与该问题直接相关的讲义内容。"
            "可以换一种问法，或确认相关章节资料是否已导入。",
            [],
        )
    best_score, best_key, best_items = sections[0]
    context = section_context(best_items)
    parts = [_first_sentences(context, limit=4, max_chars=360)]
    used: list[list[dict[str, Any]]] = [section_chunks(best_items)]
    for score, key, items in sections[1:]:
        if score < best_score * 0.8:
            break
        snippet = _first_sentences(section_context(items, max_chunks=1), limit=1, max_chars=120)
        if snippet and _is_related_snippet(snippet, query):
            parts.append(f"此外，《{key}》提到：{snippet}")
            used.append(section_chunks(items, max_chunks=1))
    answer = "\n\n".join(part for part in parts if part)
    missing = missing_identifiers(query, section_context(best_items))
    if missing:
        answer += (
            f"\n\n（说明：讲义中暂未讲到 {', '.join(missing)}，"
            "以上只回答了已有资料覆盖的部分。）"
        )

    # 引用只列真正被用到的片段：检索到但没进答案的小节不列，
    # 否则学生会看到「答案里没有的章节也标成了出处」。
    sources: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for records in used:
        for record in records:
            item = cite(record)
            key = (item["chapter_path"], item["source_file"])
            if key in seen:
                continue
            seen.add(key)
            sources.append(item)
            if len(sources) >= 3:
                return answer, sources
    return answer, sources


def compose_answer(query: str, hits: list[tuple[float, dict[str, Any]]]) -> tuple[str, list[dict[str, Any]]]:
    """抽取式回答：拼接最相关片段的开头几句，并附带引用。"""
    if not hits or hits[0][0] < MIN_SCORE:
        return (
            "当前知识库中没有检索到与该问题直接相关的讲义内容。"
            "可以换一种问法，或确认相关章节资料是否已导入。",
            [],
        )
    best_score, best = hits[0]
    parts = [_first_sentences(best.get("content", ""))]
    for score, record in hits[1:]:
        if score < best_score * 0.75:
            break
        if record.get("is_code"):
            continue
        snippet = _first_sentences(record.get("content", ""), limit=1, max_chars=120)
        if snippet:
            parts.append(f"此外，《{record.get('chapter_path') or record.get('chapter_name') or '相关章节'}》提到：{snippet}")
    answer = "\n\n".join(part for part in parts if part)
    sources: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for score, score_record in hits:
        if score < best_score * 0.6:
            continue
        item = cite(score_record)
        key = (item["chapter_path"], item["source_file"])
        if key in seen:
            continue
        seen.add(key)
        sources.append(item)
    return answer, sources[:3]


class OfflineEngine:
    """内存索引 + 任务表，供 FastAPI 端点调用。"""

    def __init__(self, corpus_dir: Path | None = None):
        self.corpus_dir = corpus_dir or Path(os.getenv("OFFLINE_CORPUS_DIR", str(DEFAULT_CORPUS)))
        self.embedder = HashingHybridEmbedder()
        self.records: list[dict[str, Any]] = []
        self.tasks: dict[str, dict[str, Any]] = {}
        self.sessions: dict[str, list[dict[str, Any]]] = {}
        self.lock = threading.Lock()

    def load(self) -> int:
        records = build_index(self.corpus_dir, self.embedder)
        with self.lock:
            self.records = records
        return len(records)

    def import_file(self, path: Path) -> dict[str, Any]:
        """把一个新资料文件解析、切分、向量化后追加进内存索引。"""
        parser = EducationDocumentParser()
        document = parser.parse(path)
        with self.lock:
            duplicated = any(record.get("file_hash") == document.file_hash for record in self.records)
        if duplicated:
            return {"status": "duplicate", "chunks": 0, "message": "该文件已导入过（内容哈希相同）"}
        chunks = CodeAwareSplitter().split(document)
        if not chunks:
            return {"status": "failed", "chunks": 0, "message": "未从资料中解析出可检索文本"}
        vectors = self.embedder.embed_documents([chunk.embedding_text() for chunk in chunks])
        records: list[dict[str, Any]] = []
        for position, chunk in enumerate(chunks):
            record = chunk.to_record()
            record["dense_vector"] = vectors["dense"][position]
            records.append(record)
        with self.lock:
            self.records.extend(records)
        return {"status": "completed", "chunks": len(records), "message": f"已导入 {len(records)} 个片段"}

    def answer(self, query: str, session_id: str = "") -> dict[str, Any]:
        sections = retrieve_sections(self.records, query)
        text, sources = compose_section_answer(query, sections)
        if session_id:
            messages = self.sessions.setdefault(session_id, [])
            messages.append({"role": "user", "content": query})
            messages.append({"role": "assistant", "content": text, "sources": sources})
        return {"answer": text, "sources": sources, "hits": len(sections)}

    def start_task(self, query: str, session_id: str) -> str:
        task_id = uuid.uuid4().hex[:16]
        self.tasks[task_id] = {"status": "running", "answer": "", "sources": [], "query": query}
        threading.Thread(target=self._run, args=(task_id, query, session_id), daemon=True).start()
        return task_id

    def _run(self, task_id: str, query: str, session_id: str) -> None:
        time.sleep(0.15)
        result = self.answer(query, session_id)
        with self.lock:
            self.tasks[task_id].update(status="completed", answer=result["answer"], sources=result["sources"])


engine = OfflineEngine()


@asynccontextmanager
async def lifespan(_: FastAPI):
    count = engine.load()
    print(f"[offline] 语料目录 {engine.corpus_dir}，已加载 {count} 个片段")
    yield


app = FastAPI(title="Java 课程辅导 · 离线降级 AI 服务", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "mode": "offline", "chunks": len(engine.records), "corpus": str(engine.corpus_dir)}


@app.post("/ai/import/start")
def start_import(payload: dict[str, Any]) -> dict[str, Any]:
    """导入一份本地资料（Spring Boot 已把上传文件落到共享目录，这里只认绝对路径）。"""
    raw = str(payload.get("fileUrl") or payload.get("path") or "").strip()
    if not raw:
        return {"code": 400, "status": "failed", "message": "fileUrl is required"}
    path = Path(raw)
    if not path.is_absolute() or not path.is_file():
        return {"code": 404, "status": "failed", "message": f"文件不存在：{raw}"}
    task_id = uuid.uuid4().hex[:16]
    try:
        result = engine.import_file(path)
    except Exception as exc:  # 解析失败也要让前端看到原因
        engine.tasks[task_id] = {"status": "failed", "kind": "import", "chunks": 0, "message": str(exc)}
        return {"code": 500, "taskId": task_id, "status": "failed", "message": str(exc)}
    engine.tasks[task_id] = {
        "status": result["status"],
        "kind": "import",
        "chunks": result["chunks"],
        "message": result["message"],
    }
    return {
        "code": 200,
        "taskId": task_id,
        "status": result["status"],
        "chunks": result["chunks"],
        "message": result["message"],
    }


@app.get("/ai/import/{task_id}/status")
def import_status(task_id: str) -> dict[str, Any]:
    task = engine.tasks.get(task_id)
    if not task or task.get("kind") != "import":
        return {"status": "not_found", "chunks": 0, "message": "任务不存在"}
    return {"status": task["status"], "chunks": task.get("chunks", 0), "message": task.get("message", "")}


@app.post("/ai/query/start")
def start_query(payload: dict[str, Any]) -> dict[str, Any]:
    query = str(payload.get("query", "")).strip()
    if not query:
        return {"code": 400, "message": "query is required"}
    session_id = str(payload.get("sessionId") or uuid.uuid4().hex)
    task_id = engine.start_task(query, session_id)
    return {"code": 200, "taskId": task_id, "sessionId": session_id}


@app.get("/ai/query/{task_id}/status")
def query_status(task_id: str) -> dict[str, Any]:
    task = engine.tasks.get(task_id)
    if not task:
        return {"status": "not_found", "answer": "", "sources": []}
    return {"status": task["status"], "answer": task["answer"], "sources": task["sources"]}


@app.get("/ai/query/{task_id}/stream")
def query_stream(task_id: str) -> StreamingResponse:
    task = engine.tasks.get(task_id, {"answer": ""})

    def generate():
        answer = task.get("answer", "")
        for start in range(0, len(answer), 12):
            yield f"data: {json.dumps({'delta': answer[start:start + 12]}, ensure_ascii=False)}\n\n"
            time.sleep(0.02)
        yield f"data: {json.dumps({'sources': task.get('sources', [])}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/ai/query/sessions")
def sessions() -> dict[str, Any]:
    return {"sessions": [{"session_id": key, "message_count": len(value)} for key, value in engine.sessions.items()]}


@app.get("/ai/query/sessions/{session_id}/messages")
def session_messages(session_id: str) -> dict[str, Any]:
    return {"messages": engine.sessions.get(session_id, [])}


@app.delete("/ai/query/sessions/{session_id}")
def delete_session(session_id: str) -> dict[str, Any]:
    engine.sessions.pop(session_id, None)
    return {"code": 200, "message": "deleted"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=int(os.getenv("OFFLINE_PORT", "9000")))
