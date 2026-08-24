from langgraph.constants import END
from langgraph.graph import StateGraph

from processor.query_processor.nodes.node_answer_output import NodeAnswerOutput
from processor.query_processor.nodes.node_query_understanding import NodeQueryUnderstanding
from processor.query_processor.nodes.node_rerank import NodeRerank
from processor.query_processor.nodes.node_rrf import NodeRrf
from processor.query_processor.nodes.node_search_embedding import NodeSearchEmbedding
from processor.query_processor.nodes.node_search_embedding_hyde import NodeSearchEmbeddingHyde
from processor.query_processor.nodes.node_web_search_mcp import NodeWebSearchMcp
from processor.query_processor.state import QueryGraphState


class KBQueryWorkflow:
    """教育问答：多轮理解 → 混合/HyDE/联网召回 → RRF → Reranker → 带引用回答。"""

    def __init__(self):
        graph = StateGraph(QueryGraphState)
        graph.add_node("node_query_understanding", NodeQueryUnderstanding())
        graph.add_node("node_multi_search", lambda state: state)
        graph.add_node("node_search_embedding", NodeSearchEmbedding())
        graph.add_node("node_search_embedding_hyde", NodeSearchEmbeddingHyde())
        graph.add_node("node_web_search_mcp", NodeWebSearchMcp())
        graph.add_node("node_join", lambda state: {})
        graph.add_node("node_rrf", NodeRrf())
        graph.add_node("node_rerank", NodeRerank())
        graph.add_node("node_answer_output", NodeAnswerOutput())
        graph.set_entry_point("node_query_understanding")
        graph.add_edge("node_query_understanding", "node_multi_search")
        graph.add_edge("node_multi_search", "node_search_embedding")
        graph.add_edge("node_multi_search", "node_search_embedding_hyde")
        graph.add_edge("node_multi_search", "node_web_search_mcp")
        graph.add_edge("node_search_embedding", "node_join")
        graph.add_edge("node_search_embedding_hyde", "node_join")
        graph.add_edge("node_web_search_mcp", "node_join")
        graph.add_edge("node_join", "node_rrf")
        graph.add_edge("node_rrf", "node_rerank")
        graph.add_edge("node_rerank", "node_answer_output")
        graph.add_edge("node_answer_output", END)
        self._app = graph.compile()

    def run(self, initial_state: QueryGraphState, stream: bool = False):
        return self._app.stream(initial_state) if stream else self._app.invoke(initial_state)
