import copy

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
    Service mô phỏng quá trình thực thi trích xuất tài liệu (Extraction Pipeline)
    có gắn kết với hệ thống Dynamic ACL Plugin qua PluggyACLPipelineDecorator.
    """

    def __init__(self, acl_mgr: DynamicACLManager = None):
        self.acl_manager = acl_mgr or get_acl_manager()

    def run_extract(self, request: ExtractRequest) -> ExtractResponse:
        """
        Thực thi pipeline trích xuất tài liệu:
        1. Tiền xử lý lọc tài liệu & nodes (RBAC, Tenant Isolation) qua `handle_input_docs`.
        2. Mô phỏng trích xuất (giữ lại các nodes hợp lệ).
        3. Hậu xử lý kết quả (PII Masking) qua `handle_output_doc`.
        """
        # Deepcopy để không làm biến đổi dữ liệu đầu vào gốc
        docs = copy.deepcopy(request.documents)
        context_dict = request.context.model_dump()

        total_input_docs = len(docs)
        total_input_nodes = sum(len(d.nodes) for d in docs)

        decorator = PluggyACLPipelineDecorator(context=context_dict)

        # 1. Chạy hook lọc input
        filtered_docs = decorator.handle_input_docs(docs)

        # 2. Chạy hook hậu xử lý output cho từng document
        final_docs = []
        for doc in filtered_docs:
            processed_doc = decorator.handle_output_doc(doc)
            final_docs.append(processed_doc)

        total_output_docs = len(final_docs)
        total_output_nodes = sum(len(d.nodes) for d in final_docs)

        return ExtractResponse(
            total_input_docs=total_input_docs,
            total_input_nodes=total_input_nodes,
            total_output_docs=total_output_docs,
            total_output_nodes=total_output_nodes,
            documents=final_docs,
        )

    def get_sample_documents(self) -> list[MockSourceDocument]:
        """
        Trả về tập dữ liệu mẫu phục vụ kiểm thử nhanh các chính sách bảo mật.
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
    """FastAPI Dependency Provider"""
    return pipeline_service
