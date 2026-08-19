from collections.abc import Iterable
from typing import Any

from app.services.acl_manager import acl_manager

try:
    from graphrag_toolkit.lexical_graph.indexing.extract.pipeline_decorator import PipelineDecorator
    from graphrag_toolkit.lexical_graph.indexing.model import SourceDocument
except ImportError:
    # Standalone Fallback nếu chạy môi trường lightweight
    class PipelineDecorator:
        def handle_input_docs(self, source_documents: Iterable[Any]) -> Iterable[Any]:
            raise NotImplementedError

        def handle_output_doc(self, source_document: Any) -> Any:
            raise NotImplementedError

    class SourceDocument:
        def __init__(self, nodes=None):
            self.nodes = list(nodes) if nodes else []


class PluggyACLPipelineDecorator(PipelineDecorator):
    """
    Adapter kết nối Pluggy ACL Manager vào cơ chế PipelineDecorator của GraphRAG-Toolkit.
    """

    def __init__(self, context: dict[str, Any] = None):
        self.context = context or {}

    def set_context(self, context: dict[str, Any]):
        self.context = context

    def handle_input_docs(
        self, source_documents: Iterable[SourceDocument]
    ) -> Iterable[SourceDocument]:
        docs = list(source_documents)
        if not docs:
            return []

        # 1. Gọi hook filter_input_docs từ các plugin
        results = acl_manager.pm.hook.filter_input_docs(docs=docs, context=self.context)
        if results:
            docs = results[-1] if results[-1] is not None else docs

        # 2. Lọc chi tiết từng Node theo quy tắc phủ quyết (veto: False in verdicts -> deny)
        filtered_docs = []
        for doc in docs:
            allowed_nodes = []
            for node in getattr(doc, "nodes", []):
                verdicts = acl_manager.pm.hook.allow_node(node=node, context=self.context)
                if False not in verdicts:
                    allowed_nodes.append(node)
            doc.nodes = allowed_nodes
            if doc.nodes:
                filtered_docs.append(doc)

        return filtered_docs

    def handle_output_doc(self, source_document: SourceDocument) -> SourceDocument:
        results = acl_manager.pm.hook.filter_output_doc(doc=source_document, context=self.context)
        return results[-1] if results and results[-1] is not None else source_document
