from pathlib import Path


def test_list_plugins(client):
    response = client.get("/api/v1/plugins")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    names = [p["name"] for p in data["plugins"]]
    assert "role_based_acl" in names
    assert "tenant_isolation_acl" in names
    assert "pii_masking_acl" in names


def test_unregister_and_active_only_filter(client):
    # 1. Unregister role_based_acl
    res = client.post("/api/v1/plugins/unregister/role_based_acl")
    assert res.status_code == 200
    assert res.json()["success"] is True

    # 2. Check full list (active_only=False, sync=False để giữ state unregister)
    list_res = client.get("/api/v1/plugins?active_only=false&sync=false")
    plugins = list_res.json()["plugins"]
    assert len(plugins) == 3
    rbac_plugin = next(p for p in plugins if p["name"] == "role_based_acl")
    assert rbac_plugin["is_active"] is False

    # 3. Check active list (active_only=True, sync=False) -> total = 2, không còn role_based_acl
    active_res = client.get("/api/v1/plugins?active_only=true&sync=false")
    active_data = active_res.json()
    assert active_data["total"] == 2
    active_names = [p["name"] for p in active_data["plugins"]]
    assert "role_based_acl" not in active_names
    assert "tenant_isolation_acl" in active_names
    assert "pii_masking_acl" in active_names

    # 4. Reset
    reset_res = client.post("/api/v1/plugins/reset")
    assert reset_res.status_code == 200
    list_res2 = client.get("/api/v1/plugins")
    assert all(p["is_active"] for p in list_res2.json()["plugins"])


def test_drop_in_plugin_discovery_and_removal(client):
    plugins_dir = Path("plugins")
    test_plugin_file = plugins_dir / "keyword_censor_plugin.py"

    try:
        # 1. Khách hàng thả file mới vào thư mục plugins/
        test_plugin_file.write_text(
            """
from app.core.acl_specs import hookimpl

class KeywordCensorPlugin:
    \"\"\"Plugin lọc từ khóa cấm\"\"\"
    @hookimpl
    def allow_node(self, node, context: dict) -> bool:
        text = getattr(node, "text", "")
        if "BANNED_KEYWORD" in text:
            return False
        return True
"""
        )

        # 2. Gọi GET /plugins (hoặc POST /plugins/sync) -> Tự động nhận diện plugin mới
        list_res = client.get("/api/v1/plugins")
        assert list_res.status_code == 200
        names = [p["name"] for p in list_res.json()["plugins"]]
        assert "keyword_censor_plugin" in names

        # 3. Chạy thử trích xuất qua pipeline -> Plugin mới có tác dụng ngay
        extract_payload = {
            "context": {"user_id": "test_user", "tenant_id": "vn", "roles": ["admin"]},
            "documents": [
                {
                    "doc_id": "doc1",
                    "nodes": [
                        {
                            "node_id": "n_banned",
                            "text": "This contains BANNED_KEYWORD inside.",
                            "metadata": {"tenant_id": "vn", "classification": "PUBLIC"},
                        },
                        {
                            "node_id": "n_clean",
                            "text": "This is clean text.",
                            "metadata": {"tenant_id": "vn", "classification": "PUBLIC"},
                        },
                    ],
                }
            ],
        }
        res = client.post("/api/v1/pipeline/extract", json=extract_payload)
        assert res.status_code == 200
        nodes = res.json()["documents"][0]["nodes"]
        assert len(nodes) == 1
        assert nodes[0]["node_id"] == "n_clean"

    finally:
        # 4. Khi xóa file khỏi plugins/ -> Hệ thống tự động gỡ bỏ plugin
        if test_plugin_file.exists():
            test_plugin_file.unlink()

        # Quét lại để xác nhận plugin đã bị gỡ
        list_res_after = client.get("/api/v1/plugins")
        names_after = [p["name"] for p in list_res_after.json()["plugins"]]
        assert "keyword_censor_plugin" not in names_after
