from pathlib import Path

from education_rag.manifest import ImportManifest
from education_rag.parsing import EducationDocumentParser
from processor.import_processor.base import BaseNode
from processor.import_processor.exceptions import FileProcessingError, StateFieldError, ValidationError
from processor.import_processor.state import ImportGraphState


class NodeEntry(BaseNode):
    """校验教育资料，并在解析前完成文件哈希幂等判断。"""
    name = "node_entry"

    def __init__(self, *args, manifest: ImportManifest | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.manifest = manifest or ImportManifest()

    def process(self, state: ImportGraphState) -> ImportGraphState:
        raw_path = state.get("import_file_path")
        if not raw_path:
            raise StateFieldError(field_name="import_file_path", message="文件路径不能为空", expected_type=str)
        path = Path(raw_path).resolve()
        if not path.is_file():
            raise FileProcessingError(message=f"文件 {path.name} 不存在")
        suffix = path.suffix.lower()
        if suffix not in EducationDocumentParser.supported_extensions:
            raise ValidationError(message=f"不支持的文件类型：{suffix}，仅支持 PDF、Markdown、DOCX")
        file_hash = EducationDocumentParser.calculate_hash(path)
        state.update(import_file_path=str(path), file_title=path.stem, source_file=path.name,
                     file_hash=file_hash, document_type=suffix.lstrip("."))
        if self.manifest.has_same_hash(path.name, file_hash):
            state.update(skipped=True, import_status="skipped", chunk_count=0)
        return state
