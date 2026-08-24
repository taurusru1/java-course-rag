from pymilvus import DataType

from config.milvus_config import milvus_config
from education_rag.manifest import ImportManifest
from processor.import_processor.base import BaseNode
from processor.import_processor.exceptions import MilvusError, StateFieldError
from processor.import_processor.state import ImportGraphState
from utils.milvus_utils import escape_milvus_string, get_milvus_client


class NodeImportMilvus(BaseNode):
    """按来源替换教育切片，并在成功后记录文件哈希。"""
    name = "node_import_milvus"

    def __init__(self, *args, manifest: ImportManifest | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.manifest = manifest or ImportManifest()

    def process(self, state: ImportGraphState) -> ImportGraphState:
        chunks = state.get("chunks") or []
        if not chunks:
            raise StateFieldError(field_name="chunks", message="入库切片不能为空")
        first = chunks[0]
        if not first.get("dense_vector") or first.get("sparse_vector") is None:
            raise StateFieldError(field_name="chunks", message="切片缺少 BGE-M3 向量")
        collection = milvus_config.chunks_collection
        if not collection:
            raise MilvusError("未配置 CHUNKS_COLLECTION")
        client = get_milvus_client()
        if not client.has_collection(collection):
            self._create_collection(client, collection, len(first["dense_vector"]))
        source_file = escape_milvus_string(state["source_file"])
        client.delete(collection_name=collection, filter=f'source_file == "{source_file}"')
        client.insert(collection_name=collection, data=chunks)
        self.manifest.record(state["source_file"], state["file_hash"], len(chunks))
        state.update(import_status="imported", chunk_count=len(chunks))
        return state

    @staticmethod
    def _create_collection(client, collection: str, vector_dimension: int) -> None:
        schema = client.create_schema(auto_id=False, enable_dynamic_field=False)
        schema.add_field("chunk_id", DataType.VARCHAR, is_primary=True, max_length=64)
        schema.add_field("content", DataType.VARCHAR, max_length=65535)
        schema.add_field("file_hash", DataType.VARCHAR, max_length=64)
        schema.add_field("part", DataType.INT32)
        for field in ("content_type", "course_name", "project_name", "chapter_name", "chapter_path",
                      "question_bank_name", "question_id", "question_type", "source_file"):
            schema.add_field(field, DataType.VARCHAR, max_length=1024)
        schema.add_field("knowledge_points", DataType.ARRAY, element_type=DataType.VARCHAR,
                         max_capacity=32, max_length=256)
        schema.add_field("page_number", DataType.INT32)
        schema.add_field("sparse_vector", DataType.SPARSE_FLOAT_VECTOR)
        schema.add_field("dense_vector", DataType.FLOAT_VECTOR, dim=vector_dimension)
        indexes = client.prepare_index_params()
        indexes.add_index("dense_vector", index_name="dense_vector_index", index_type="AUTOINDEX", metric_type="COSINE")
        indexes.add_index("sparse_vector", index_name="sparse_vector_index", index_type="SPARSE_INVERTED_INDEX",
                          metric_type="IP", params={"inverted_index_algo": "DAAT_MAXSCORE"})
        client.create_collection(collection_name=collection, schema=schema, index_params=indexes)
