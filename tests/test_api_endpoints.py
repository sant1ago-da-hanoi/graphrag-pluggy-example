def test_health_check(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_get_plugins_list(client):
    response = client.get("/api/v1/plugins")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    names = [p["name"] for p in data["plugins"]]
    assert "role_based_acl" in names
    assert "tenant_isolation_acl" in names
    assert "pii_masking_acl" in names


def test_get_sample_docs(client):
    response = client.get("/api/v1/pipeline/sample-docs")
    assert response.status_code == 200
    docs = response.json()
    assert len(docs) == 2


def test_extract_api_flow(client):
    # 1. Lấy sample docs
    docs_res = client.get("/api/v1/pipeline/sample-docs")
    docs = docs_res.json()

    # 2. Gửi request extract với user thường tenant VN
    payload = {
        "context": {
            "user_id": "test_viewer",
            "tenant_id": "vn",
            "roles": ["viewer"],
        },
        "documents": docs,
    }
    res = client.post("/api/v1/pipeline/extract", json=payload)
    assert res.status_code == 200
    res_data = res.json()

    assert res_data["total_input_docs"] == 2
    assert res_data["total_output_docs"] == 1
    assert res_data["total_output_nodes"] == 1
    assert "[REDACTED_EMAIL]" in res_data["documents"][0]["nodes"][0]["text"]


def test_unregister_and_reextract(client):
    # Gỡ bỏ PII plugin
    unreg_res = client.post("/api/v1/plugins/unregister/pii_masking_acl")
    assert unreg_res.status_code == 200

    # Chạy lại extract -> PII không còn bị mask
    docs_res = client.get("/api/v1/pipeline/sample-docs")
    payload = {
        "context": {
            "user_id": "test_viewer",
            "tenant_id": "vn",
            "roles": ["viewer"],
        },
        "documents": docs_res.json(),
    }
    res = client.post("/api/v1/pipeline/extract", json=payload)
    assert res.status_code == 200
    res_data = res.json()
    assert "ceo@company.vn" in res_data["documents"][0]["nodes"][0]["text"]
