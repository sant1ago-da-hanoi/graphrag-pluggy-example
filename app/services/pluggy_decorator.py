from collections.abc import Iterable
from typing import Any

from graphrag_toolkit.lexical_graph.indexing.extract.pipeline_decorator import PipelineDecorator
from graphrag_toolkit.lexical_graph.indexing.model import SourceDocument

from app.services.acl_manager import acl_manager


class PluggyACLPipelineDecorator(PipelineDecorator):
    """
    Adapter kết nối Pluggy ACL Manager vào cơ chế PipelineDecorator chính thức của GraphRAG-Toolkit.
    """

    def __init__(self, context: dict[str, Any] = None):
        self.context = context or {}

    def set_context(self, context: dict[str, Any]):
        self.context = context

    def handle_input_docs(
        self, source_documents: Iterable[SourceDocument]
    ) -> Iterable[SourceDocument]:
        """
        Điểm chặn tiền xử lý (Input Filter) của GraphRAG:
        1. Gọi hook filter_input_docs.
        2. Lọc chi tiết từng Node theo Veto Rule (allow_node).
        """
        docs = list(source_documents)
        if not docs:
            return []

        # 1. Hook lọc danh sách documents
        results = acl_manager.pm.hook.filter_input_docs(docs=docs, context=self.context)
        if results:
            docs = results[-1] if results[-1] is not None else docs

        # 2. Lọc chi tiết từng Node
        filtered_docs = []
        for doc in docs:
            target_nodes = getattr(doc, "nodes", []) or []
            if not target_nodes and getattr(doc, "refNode", None):
                target_nodes = [doc.refNode]

            allowed_nodes = []
            for node in target_nodes:
                verdicts = acl_manager.pm.hook.allow_node(node=node, context=self.context)
                if False not in verdicts:
                    allowed_nodes.append(node)

            doc.nodes = allowed_nodes
            # Nếu còn ít nhất 1 node được phép -> Cho phép document đi tiếp vào pipeline
            if doc.nodes:
                filtered_docs.append(doc)

        return filtered_docs

    def handle_output_doc(self, source_document: SourceDocument) -> SourceDocument:
        """
        Điểm chặn hậu xử lý (Output Post-processing) của GraphRAG:
        Gọi hook filter_output_doc để che giấu PII hoặc sửa đổi metadata/text.
        """
        results = acl_manager.pm.hook.filter_output_doc(doc=source_document, context=self.context)
        return results[-1] if results and results[-1] is not None else source_document
