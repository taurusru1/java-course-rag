"""MongoDB 多轮历史；连接采用懒加载，数据库不可用时调用方可降级。"""

import logging
import os
from datetime import datetime
from typing import Any

from bson import ObjectId
from dotenv import load_dotenv
from pymongo import ASCENDING, MongoClient

load_dotenv()


class HistoryMongoTool:
    def __init__(self):
        mongo_url = os.getenv("MONGO_URL")
        db_name = os.getenv("MONGO_DB_NAME")
        if not mongo_url or not db_name:
            raise RuntimeError("未配置 MONGO_URL 或 MONGO_DB_NAME")
        self.client = MongoClient(mongo_url, serverSelectionTimeoutMS=2000)
        self.chat_message = self.client[db_name]["chat_message"]
        self.chat_message.create_index([("session_id", 1), ("ts", -1)])


_history_mongo_tool: HistoryMongoTool | None = None


def get_history_mongo_tool() -> HistoryMongoTool:
    global _history_mongo_tool
    if _history_mongo_tool is None:
        _history_mongo_tool = HistoryMongoTool()
    return _history_mongo_tool


def save_chat_message(
    session_id: str,
    role: str,
    text: str,
    rewritten_query: str = "",
    metadata_filters: dict | None = None,
    citations: list[dict] | None = None,
    image_urls: list[str] | None = None,
    message_id: str | None = None,
) -> str:
    document = {
        "session_id": session_id, "role": role, "text": text,
        "rewritten_query": rewritten_query or "", "metadata_filters": metadata_filters or {},
        "citations": citations or [], "image_urls": image_urls or [],
        "ts": datetime.now().timestamp(),
    }
    collection = get_history_mongo_tool().chat_message
    if message_id:
        collection.update_one({"_id": ObjectId(message_id)}, {"$set": document})
        return message_id
    return str(collection.insert_one(document).inserted_id)


def get_recent_messages(session_id: str, limit: int = 10) -> list[dict[str, Any]]:
    try:
        cursor = get_history_mongo_tool().chat_message.find({"session_id": session_id}).sort("ts", ASCENDING).limit(limit)
        return list(cursor)
    except Exception as exc:
        logging.warning("MongoDB 历史查询不可用：%s", exc)
        return []


def clear_history(session_id: str) -> int:
    try:
        return get_history_mongo_tool().chat_message.delete_many({"session_id": session_id}).deleted_count
    except Exception as exc:
        logging.warning("MongoDB 历史清理不可用：%s", exc)
        return 0
