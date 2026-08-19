from app.schemas.pipeline_schema import (
    ExtractRequest,
    UserContext,
)
from app.services.acl_manager import get_acl_manager
from app.services.pipeline_service import PipelineService


def test_pipeline_service_full_flow():
    acl_mgr = get_acl_manager()
    acl_mgr.reset()
    service = PipelineService(acl_mgr=acl_mgr)

    samples = service.get_sample_documents()

    # Kịch bản 1: User thường của tenant VN (role: viewer)
    req1 = ExtractRequest(
        context=UserContext(user_id="user_vn", tenant_id="vn", roles=["viewer"]),
        documents=samples,
    )
    res1 = service.run_extract(req1)

    # Giải thích kết quả:
    # - Document US bị loại bỏ hoàn toàn (vì tenant US != tenant VN)
    # - Node restricted VN bị loại bỏ (vì role viewer không phải admin)
    # - Node public VN được giữ lại nhưng email/phone bị mask
    assert res1.total_input_docs == 2
    assert res1.total_input_nodes == 3
    assert res1.total_output_docs == 1
    assert res1.total_output_nodes == 1

    node = res1.documents[0].nodes[0]
    assert node.node_id == "node_public_vn"
    assert "[REDACTED_EMAIL]" in node.text
    assert "[REDACTED_PHONE]" in node.text

    # Kịch bản 2: Admin của tenant VN (role: admin)
    req2 = ExtractRequest(
        context=UserContext(user_id="admin_vn", tenant_id="vn", roles=["admin"]),
        documents=samples,
    )
    res2 = service.run_extract(req2)

    # Admin VN xem được cả 2 nodes của VN (public + restricted), nhưng US vẫn bị chặn
    assert res2.total_output_docs == 1
    assert res2.total_output_nodes == 2
    node_ids = [n.node_id for n in res2.documents[0].nodes]
    assert "node_public_vn" in node_ids
    assert "node_restricted_vn" in node_ids
    # Admin có quyền xem raw PII không bị mask
    assert "ceo@company.vn" in res2.documents[0].nodes[0].text
