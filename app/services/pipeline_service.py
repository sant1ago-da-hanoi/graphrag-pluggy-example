
from graphrag_toolkit.lexical_graph.indexing.extract.extraction_pipeline import ExtractionPipeline
from graphrag_toolkit.lexical_graph.indexing.model import SourceDocument
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import Document

from app.schemas.pipeline_schema import (
    ExtractRequest,
    ExtractResponse,
    MockNode,
    MockSourceDocument,
)
from app.services.acl_manager import DynamicACLManager, get_acl_manager
from app.services.pluggy_decorator import PluggyACLPipelineDecorator


class PipelineService:
    """
    Service trích xuất tài liệu tích hợp trực tiếp với ExtractionPipeline thực tế
    của GraphRAG-Toolkit thông qua PluggyACLPipelineDecorator.
    """

    def __init__(self, acl_mgr: DynamicACLManager = None):
        self.acl_manager = acl_mgr or get_acl_manager()

    def run_extract(self, request: ExtractRequest) -> ExtractResponse:
        """
        Thực thi trích xuất tài liệu qua ExtractionPipeline THẬT của GraphRAG-Toolkit:
        1. Chuyển đổi payload thành LlamaIndex Document & GraphRAG SourceDocument.
        2. Chạy qua ExtractionPipeline (kèm SentenceSplitter chunker và PluggyACLPipelineDecorator).
        3. Decorator kích hoạt các Pluggy hooks:
           - Tiền xử lý (handle_input_docs): Lọc tài liệu theo RBAC và Tenant Isolation.
           - Xử lý GraphRAG: Chia nhỏ chunking và trích xuất.
           - Hậu xử lý (handle_output_doc): Che giấu thông tin nhạy cảm PII.
        """
        context_dict = request.context.model_dump()
        total_input_docs = len(request.documents)
        total_input_nodes = sum(len(d.nodes) for d in request.documents)

        # Chuyển đổi sang GraphRAG SourceDocuments thật
        source_docs: list[SourceDocument] = []
        for req_doc in request.documents:
            doc_nodes = []
            for req_node in req_doc.nodes:
                meta = dict(req_node.metadata)
                meta["original_id"] = req_node.node_id
                meta["doc_id"] = req_doc.doc_id or "default_doc"
                doc_obj = Document(
                    text=req_node.text,
                    metadata=meta,
                    id_=req_node.node_id,
                )
                doc_nodes.append(doc_obj)
            if doc_nodes:
                source_docs.append(SourceDocument(refNode=doc_nodes[0], nodes=doc_nodes))

        # Cắm PluggyACLPipelineDecorator vào ExtractionPipeline của GraphRAG
        decorator = PluggyACLPipelineDecorator(context=context_dict)
        splitter = SentenceSplitter(chunk_size=500, chunk_overlap=50)

        pipeline = ExtractionPipeline(
            components=[splitter],
            extraction_decorator=decorator,
            num_workers=1,
            show_progress=False,
        )

        # Chạy pipeline thật của GraphRAG-Toolkit
        extracted_source_docs = list(pipeline.extract(source_docs))

        # Gom các nodes đầu ra theo doc_id
        docs_map: dict[str, list[MockNode]] = {}
        for s_doc in extracted_source_docs:
            for n in getattr(s_doc, "nodes", []):
                d_id = n.metadata.get("doc_id", "default_doc")
                node_id = n.metadata.get("original_id", getattr(n, "node_id", "node"))
                if d_id not in docs_map:
                    docs_map[d_id] = []
                # Làm sạch metadata trả về
                clean_meta = {
                    k: v for k, v in n.metadata.items()
                    if not k.startswith("__aws__") and k not in ["original_id", "doc_id"]
                }
                docs_map[d_id].append(
                    MockNode(
                        node_id=node_id,
                        text=n.text if hasattr(n, "text") else str(n),
                        metadata=clean_meta,
                    )
                )

        final_documents = [
            MockSourceDocument(doc_id=d_id, nodes=nodes)
            for d_id, nodes in docs_map.items()
        ]

        total_output_docs = len(final_documents)
        total_output_nodes = sum(len(d.nodes) for d in final_documents)

        return ExtractResponse(
            total_input_docs=total_input_docs,
            total_input_nodes=total_input_nodes,
            total_output_docs=total_output_docs,
            total_output_nodes=total_output_nodes,
            documents=final_documents,
        )

    def get_sample_documents(self) -> list[MockSourceDocument]:
        """
        Dữ liệu tài liệu mẫu thực tế phục vụ kiểm thử.
        """
        return [
            MockSourceDocument(
                doc_id="sample_doc_vn",
                nodes=[
                    MockNode(
                        node_id="node_public_vn",
                        text="Báo cáo công khai chi nhánh VN: Doanh thu Q2 tăng 25%. Liên hệ CEO: ceo@company.vn hoặc SĐT: +84 901 234 567 để biết thêm chi tiết.",
                        metadata={"classification": "PUBLIC", "tenant_id": "vn"},
                    ),
                    MockNode(
                        node_id="node_restricted_vn",
                        text="Tài liệu TUYỆT MẬT VN: Kế hoạch sáp nhập đối thủ cạnh tranh giá trị 50 triệu USD vào tháng 12.",
                        metadata={"classification": "RESTRICTED", "tenant_id": "vn"},
                    ),
                ],
            ),
            MockSourceDocument(
                doc_id="sample_doc_us",
                nodes=[
                    MockNode(
                        node_id="node_us_tenant",
                        text="US Branch Operations: US operations expanded to New York. Contact: ops@company.us or +1 (555) 019-2834.",
                        metadata={"classification": "PUBLIC", "tenant_id": "us"},
                    ),
                ],
            ),
        ]


pipeline_service = PipelineService()


def get_pipeline_service() -> PipelineService:
    return pipeline_service
