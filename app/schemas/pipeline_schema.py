from typing import Any

from pydantic import BaseModel, Field


class MockNode(BaseModel):
    node_id: str = Field(..., description="ID định danh của Node")
    text: str = Field(..., description="Nội dung văn bản của Node")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Metadata kèm theo (classification, tenant_id,...)"
    )


class MockSourceDocument(BaseModel):
    doc_id: str | None = Field(None, description="ID định danh của Document (tùy chọn)")
    nodes: list[MockNode] = Field(
        default_factory=list, description="Danh sách các Nodes thuộc Document"
    )


class UserContext(BaseModel):
    user_id: str = Field(..., description="ID người dùng gửi request")
    tenant_id: str | None = Field("vn", description="ID tenant của người dùng")
    roles: list[str] = Field(
        default_factory=lambda: ["viewer"], description="Danh sách các vai trò (roles)"
    )
    permissions: list[str] = Field(
        default_factory=list, description="Danh sách các quyền hạn cụ thể (permissions)"
    )


class ExtractRequest(BaseModel):
    context: UserContext = Field(..., description="Ngữ cảnh bảo mật của người dùng")
    documents: list[MockSourceDocument] = Field(
        ..., description="Danh sách các tài liệu cần trích xuất qua pipeline"
    )


class ExtractResponse(BaseModel):
    total_input_docs: int = Field(..., description="Tổng số documents đầu vào")
    total_input_nodes: int = Field(..., description="Tổng số nodes đầu vào")
    total_output_docs: int = Field(..., description="Tổng số documents sau khi qua bộ lọc ACL")
    total_output_nodes: int = Field(..., description="Tổng số nodes sau khi qua bộ lọc ACL")
    documents: list[MockSourceDocument] = Field(
        ..., description="Danh sách documents và nodes đầu ra (đã áp dụng PII masking)"
    )
