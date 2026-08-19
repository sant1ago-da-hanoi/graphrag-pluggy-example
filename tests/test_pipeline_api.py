def test_scenario_standard_user_vn(client):
    """
    Kịch bản 1: User thường của tenant VN (role: viewer)
    - Chỉ thấy node public của VN.
    - Node restricted bị chặn bởi RBAC.
    - Tenant US bị chặn bởi Tenant Isolation.
    - Email và số điện thoại bị che giấu bởi PII Masking.
    """
    docs = client.get("/api/v1/pipeline/sample-docs").json()

    payload = {
        "context": {
            "user_id": "viewer_vn",
            "tenant_id": "vn",
            "roles": ["viewer"],
        },
        "documents": docs,
    }
    res = client.post("/api/v1/pipeline/extract", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["total_output_docs"] == 1
    assert data["total_output_nodes"] == 1
    node = data["documents"][0]["nodes"][0]
    assert node["node_id"] == "node_public_vn"
    assert "[REDACTED_EMAIL]" in node["text"]
    assert "[REDACTED_PHONE]" in node["text"]


def test_scenario_admin_user_vn(client):
    """
    Kịch bản 2: Admin của tenant VN (role: admin)
    - Thấy cả node public & restricted của VN.
    - Tenant US vẫn bị chặn bởi Tenant Isolation.
    - Admin có quyền xem raw PII không bị che giấu.
    """
    docs = client.get("/api/v1/pipeline/sample-docs").json()

    payload = {
        "context": {
            "user_id": "admin_vn",
            "tenant_id": "vn",
            "roles": ["admin"],
        },
        "documents": docs,
    }
    res = client.post("/api/v1/pipeline/extract", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["total_output_docs"] == 1
    assert data["total_output_nodes"] == 2
    node_ids = [n["node_id"] for n in data["documents"][0]["nodes"]]
    assert "node_public_vn" in node_ids
    assert "node_restricted_vn" in node_ids

    # Kiểm tra PII không bị che
    pub_node = next(n for n in data["documents"][0]["nodes"] if n["node_id"] == "node_public_vn")
    assert "ceo@company.vn" in pub_node["text"]
    assert "+84 901 234 567" in pub_node["text"]


def test_scenario_superadmin_all_tenants(client):
    """
    Kịch bản 3: Superadmin (role: superadmin)
    - Được phép xem dữ liệu của TẤT CẢ các tenants (VN + US).
    """
    docs = client.get("/api/v1/pipeline/sample-docs").json()

    payload = {
        "context": {
            "user_id": "superadmin",
            "tenant_id": "vn",
            "roles": ["superadmin", "admin"],
        },
        "documents": docs,
    }
    res = client.post("/api/v1/pipeline/extract", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["total_output_docs"] == 2
    assert data["total_output_nodes"] == 3


def test_scenario_dynamic_unregistration_effects(client):
    """
    Kịch bản 4: Gỡ bỏ từng plugin động và kiểm tra tác động tức thì:
    1. Gỡ bỏ RBAC -> user thường xem được restricted node.
    2. Gỡ bỏ Tenant Isolation -> user VN xem được tài liệu của tenant US.
    3. Gỡ bỏ PII Masking -> user thường xem được email/phone gốc.
    """
    docs = client.get("/api/v1/pipeline/sample-docs").json()
    viewer_payload = {
        "context": {
            "user_id": "viewer_vn",
            "tenant_id": "vn",
            "roles": ["viewer"],
        },
        "documents": docs,
    }

    # 1. Unregister RBAC
    client.post("/api/v1/plugins/unregister/role_based_acl")
    res1 = client.post("/api/v1/pipeline/extract", json=viewer_payload)
    nodes1 = [n["node_id"] for n in res1.json()["documents"][0]["nodes"]]
    assert "node_restricted_vn" in nodes1

    # 2. Unregister Tenant Isolation
    client.post("/api/v1/plugins/unregister/tenant_isolation_acl")
    res2 = client.post("/api/v1/pipeline/extract", json=viewer_payload)
    assert res2.json()["total_output_docs"] == 2
    all_node_ids = [n["node_id"] for doc in res2.json()["documents"] for n in doc["nodes"]]
    assert "node_us_tenant" in all_node_ids

    # 3. Unregister PII Masking
    client.post("/api/v1/plugins/unregister/pii_masking_acl")
    res3 = client.post("/api/v1/pipeline/extract", json=viewer_payload)
    pub_node = next(
        n
        for doc in res3.json()["documents"]
        for n in doc["nodes"]
        if n["node_id"] == "node_public_vn"
    )
    assert "ceo@company.vn" in pub_node["text"]
