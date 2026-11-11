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
import threading
import time
import uuid
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


def build_index(corpus_dir: Path, embedder: HashingHybridEmbedder) -> list[dict[str, Any]]:
    """解析语料目录，返回带向量与元数据的片段列表。"""
    parser = EducationDocumentParser()
    splitter = CodeAwareSplitter()
    records: list[dict[str, Any]] = []
    if not corpus_dir.exists():
        return records
    for path in sorted(corpus_dir.rglob("*.md")):
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
    """按哈希向量余弦相似度召回，返回 [(score, record)]，已按分数降序。"""
    if not records or not query.strip():
        return []
    return _rank(records, query, top_k)


def _rank(records: list[dict[str, Any]], query: str, top_k: int) -> list[tuple[float, dict[str, Any]]]:
    """混合打分：0.5 × 向量余弦 + 0.5 × 词面重合率。

    纯哈希向量在中文上区分度有限，加一路词面信号可以让「问什么就排什么」
    更稳定，这也是评测里「混合检索」的最简基线。
    """
    embedder = HashingHybridEmbedder()
    query_vector = embedder.embed_documents([query])["dense"][0]
    query_tokens = set(embedder.tokens(query))
    scored = []
    for record in records:
        semantic = cosine(query_vector, record.get("dense_vector") or [])
        text_tokens = set(embedder.tokens(record.get("content", "")))
        overlap = len(query_tokens & text_tokens) / len(query_tokens) if query_tokens else 0.0
        scored.append((0.5 * semantic + 0.5 * overlap, record))
    scored.sort(key=lambda item: item[0], reverse=True)
    return scored[:top_k]


def _first_sentences(text: str, limit: int = 3, max_chars: int = 300) -> str:
    """取片段开头的若干句，用于抽取式回答。"""
    cleaned = " ".join(line.strip() for line in text.splitlines() if line.strip())
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

    def answer(self, query: str, session_id: str = "") -> dict[str, Any]:
        hits = search(self.records, query)
        text, sources = compose_answer(query, hits)
        if session_id:
            messages = self.sessions.setdefault(session_id, [])
            messages.append({"role": "user", "content": query})
            messages.append({"role": "assistant", "content": text, "sources": sources})
        return {"answer": text, "sources": sources, "hits": len(hits)}

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
