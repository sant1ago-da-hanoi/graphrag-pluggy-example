from fastapi import APIRouter, Depends

from app.schemas.pipeline_schema import (
    ExtractRequest,
    ExtractResponse,
    MockSourceDocument,
)
from app.services.pipeline_service import PipelineService, get_pipeline_service

router = APIRouter(prefix="/pipeline", tags=["GraphRAG Pipeline Execution"])


@router.get(
    "/sample-docs", response_model=list[MockSourceDocument], summary="Lấy dữ liệu tài liệu mẫu"
)
def get_sample_docs(
    pipeline_svc: PipelineService = Depends(get_pipeline_service),
) -> list[MockSourceDocument]:
    """
    Trả về bộ dữ liệu mẫu (public vn, restricted vn, us tenant) phục vụ việc test nhanh trên Swagger.
    """
    return pipeline_svc.get_sample_documents()


@router.post(
    "/extract",
    response_model=ExtractResponse,
    summary="Chạy thử nghiệm Pipeline trích xuất tài liệu",
)
def extract_documents(
    request: ExtractRequest,
    pipeline_svc: PipelineService = Depends(get_pipeline_service),
) -> ExtractResponse:
    """
    Thực thi luồng trích xuất tài liệu:
    1. Lọc quyền đầu vào trên Document & Node (RBAC, Tenant Isolation).
    2. Hậu xử lý che giấu thông tin nhạy cảm (PII Masking).
    """
    return pipeline_svc.run_extract(request)
