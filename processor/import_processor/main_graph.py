"""教育资料导入 LangGraph：解析 → 切分 → BGE-M3 → Milvus。"""

from langgraph.constants import END
from langgraph.graph import StateGraph

from processor.import_processor.nodes.node_bge_embedding import NodeBGEEmbedding
from processor.import_processor.nodes.node_document_parse import NodeDocumentParse
from processor.import_processor.nodes.node_document_split import NodeDocumentSplit
from processor.import_processor.nodes.node_enrty import NodeEntry
from processor.import_processor.nodes.node_import_milvus import NodeImportMilvus
from processor.import_processor.state import ImportGraphState


class KBImportWorkflow:
    def __init__(self):
        self._compiled_graph = None

    @property
    def graph(self):
        if self._compiled_graph is None:
            self._compiled_graph = self.build_graph()
        return self._compiled_graph

    @staticmethod
    def build_graph():
        graph = StateGraph(ImportGraphState)
        graph.add_node("node_entry", NodeEntry())
        graph.add_node("node_document_parse", NodeDocumentParse())
        graph.add_node("node_document_split", NodeDocumentSplit())
        graph.add_node("node_bge_embedding", NodeBGEEmbedding())
        graph.add_node("node_import_milvus", NodeImportMilvus())
        graph.set_entry_point("node_entry")
        graph.add_conditional_edges("node_entry", lambda state: END if state.get("skipped") else "parse",
                                    {END: END, "parse": "node_document_parse"})
        graph.add_edge("node_document_parse", "node_document_split")
        graph.add_edge("node_document_split", "node_bge_embedding")
        graph.add_edge("node_bge_embedding", "node_import_milvus")
        graph.add_edge("node_import_milvus", END)
        return graph.compile()

    def run(self, state: ImportGraphState, stream: bool = False):
        return self.graph.stream(state) if stream else self.graph.invoke(state)
