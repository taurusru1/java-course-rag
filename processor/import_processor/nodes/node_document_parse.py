from education_rag.parsing import EducationDocumentParser
from processor.import_processor.base import BaseNode
from processor.import_processor.state import ImportGraphState


class NodeDocumentParse(BaseNode):
    """统一解析 PDF、Markdown 和 DOCX。"""
    name = "node_document_parse"

    def __init__(self, *args, parser: EducationDocumentParser | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser = parser or EducationDocumentParser()

    def process(self, state: ImportGraphState) -> ImportGraphState:
        state["parsed_document"] = self.parser.parse(state["import_file_path"])
        state["import_status"] = "parsed"
        return state
