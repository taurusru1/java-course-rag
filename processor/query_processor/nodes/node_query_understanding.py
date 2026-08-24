from processor.query_processor.base import NodeBase
from processor.query_processor.state import QueryGraphState
from utils.mongo_history_utils import get_recent_messages, save_chat_message
from utils.task_utils import add_done_task


class NodeQueryUnderstanding(NodeBase):
    """结合 MongoDB 历史将当前问题改写成可独立检索的问题。"""
    name = "node_query_understanding"

    def process(self, state: QueryGraphState) -> QueryGraphState:
        query = (state.get("original_query") or "").strip()
        history = get_recent_messages(state["session_id"], limit=8)
        filters = dict(state.get("metadata_filters") or {})
        if "题" in query and "content_type" not in filters:
            filters["content_type"] = "question"
        elif "项目" in query and "content_type" not in filters:
            filters["content_type"] = "project_material"
        elif any(word in query for word in ("课程介绍", "有哪些课程", "推荐课程")) and "content_type" not in filters:
            filters["content_type"] = "course_intro"

        recent_user = next((m.get("text", "") for m in reversed(history) if m.get("role") == "user"), "")
        has_reference = any(word in query for word in ("这个", "它", "上述", "刚才", "该课程", "该项目"))
        rewritten = f"上一个问题：{recent_user}\n当前问题：{query}" if has_reference and recent_user else query
        try:
            message_id = save_chat_message(
                state["session_id"], "user", query, rewritten_query=rewritten,
                metadata_filters=filters,
            )
        except Exception:
            message_id = ""
        state.update(history=history, rewritten_query=rewritten, metadata_filters=filters, message_id=message_id)
        add_done_task(state["session_id"], self.name, state.get("is_stream"))
        return state
