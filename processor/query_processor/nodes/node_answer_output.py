import json
from typing import Any

from education_rag.models import citation_from_record
from processor.query_processor.base import NodeBase
from processor.query_processor.prompt.answer_prompt import ANSWER_PROMPT
from processor.query_processor.state import QueryGraphState
from tool.logger import logger
from utils.llm_utils import get_llm_client
from utils.mongo_history_utils import save_chat_message
from utils.sse_utils import SSEEvent, push_to_session
from utils.task_utils import add_done_task, set_task_result


class NodeAnswerOutput(NodeBase):
    name = "node_answer_output"

    def process(self, state: QueryGraphState) -> QueryGraphState:
        documents = state.get("reranked_docs") or []
        citations = self._citations(documents)
        state["citations"] = citations
        if not documents:
            answer = "当前知识库资料不足，未检索到能够回答该问题的课程、项目或题目内容。"
            state["answer"] = answer
            if state.get("is_stream"):
                push_to_session(state["session_id"], SSEEvent.DELTA, {"delta": answer})
        else:
            prompt = self._build_prompt(state, documents)
            state["prompt"] = prompt
            self._generate(state, prompt)
        self._save_history(state)
        set_task_result(state["session_id"], "answer", state.get("answer", ""))
        set_task_result(state["session_id"], "citations", citations)
        add_done_task(state["session_id"], self.name, state.get("is_stream"))
        if state.get("is_stream"):
            push_to_session(state["session_id"], SSEEvent.FINAL, {
                "answer": state.get("answer", ""), "citations": citations, "status": "completed",
            })
        return state

    @staticmethod
    def _citations(documents: list[dict]) -> list[dict[str, Any]]:
        citations = []
        for doc in documents:
            if doc.get("source") == "web":
                citations.append({"source": "web", "title": doc.get("title", ""), "url": doc.get("url", "")})
            else:
                citations.append(citation_from_record(doc))
        return citations

    @staticmethod
    def _build_prompt(state: QueryGraphState, documents: list[dict]) -> str:
        context_parts = []
        for index, doc in enumerate(documents, start=1):
            metadata = {key: doc.get(key) for key in (
                "source", "chunk_id", "course_name", "project_name", "chapter_path",
                "source_file", "page_number", "url",
            ) if doc.get(key) not in (None, "")}
            context_parts.append(f"[{index}] {json.dumps(metadata, ensure_ascii=False)}\n{doc['content']}")
        history = "\n".join(f"{m.get('role')}: {m.get('text')}" for m in state.get("history") or [])
        return ANSWER_PROMPT.format(
            context="\n\n".join(context_parts), history=history or "暂无",
            metadata_filters=json.dumps(state.get("metadata_filters") or {}, ensure_ascii=False),
            question=state["rewritten_query"],
        )

    @staticmethod
    def _generate(state: QueryGraphState, prompt: str) -> None:
        try:
            llm = get_llm_client()
            if state.get("is_stream"):
                answer = ""
                for chunk in llm.stream(prompt):
                    delta = getattr(chunk, "content", "") or ""
                    if delta:
                        answer += delta
                        push_to_session(state["session_id"], SSEEvent.DELTA, {"delta": delta})
                state["answer"] = answer
            else:
                state["answer"] = llm.invoke(prompt).content
        except Exception as exc:
            logger.exception(f"答案生成失败：{exc}")
            state["answer"] = "已检索到相关资料，但当前大模型服务不可用，请稍后重试。"

    @staticmethod
    def _save_history(state: QueryGraphState) -> None:
        try:
            save_chat_message(
                state["session_id"], "assistant", state.get("answer", ""),
                metadata_filters=state.get("metadata_filters") or {}, citations=state.get("citations") or [],
            )
        except Exception as exc:
            logger.warning(f"MongoDB 历史写入失败，不影响本轮回答：{exc}")
