# FastAPI Dynamic ACL Plugin Showcase for GraphRAG-Toolkit

Ứng dụng REST API xây dựng bằng **FastAPI** và **Pluggy** nhằm trình diễn và quản lý cơ chế **Dynamic Drop-in Plugins**
tích hợp trực tiếp vào **Extraction Pipeline** của **GraphRAG-Toolkit** (`graphrag-lexical-graph`).

---

## 🎯 Giá Trị Cốt Lõi (Core Value Proposition)

> **"Khách hàng chỉ cần thả (copy) bất kỳ file Python `.py` nào vào thư mục `plugins/` $\rightarrow$ Hệ thống tự động
nhận diện, kích hoạt và áp dụng ngay lập tức vào GraphRAG Pipeline mà KHÔNG cần khởi động lại server, KHÔNG cần sửa core
codebase."**

---

## 🌟 Tính Năng Nổi Bật

1. **📂 Drop-in Plugin Architecture (Zero Config & Zero Downtime)**:
    - Thư mục `plugins/` đóng vai trò là kho plugin sống.
    - Thả file mới vào `plugins/` $\rightarrow$ Hệ thống **tự động nạp (Auto-Discover & Load)**.
    - Sửa code trong file $\rightarrow$ Hệ thống **tự động Hot-Reload version mới**.
    - Xóa file khỏi `plugins/` $\rightarrow$ Hệ thống **tự động gỡ bỏ (Unregister)**.
2. **🛡️ Kiểm Soát Truy Cập Đa Tầng (Multi-layer ACL)**:
    - **Role-Based Access Control (RBAC)**: Lọc các Node có nhãn bảo mật `RESTRICTED` hoặc `CONFIDENTIAL` theo danh sách
      `roles` của người dùng.
    - **Tenant Isolation**: Ngăn chặn rò rỉ dữ liệu giữa các tổ chức (`tenant_id`), bảo vệ kiến trúc SaaS.
    - **PII Masking**: Tự động che giấu số điện thoại (`[REDACTED_PHONE]`) và email (`[REDACTED_EMAIL]`) ở bước xuất kết
      quả đối với người dùng thông thường.
3. **⚡ Chuẩn PyPI**:
    - Sử dụng package chính thức `graphrag-lexical-graph` và `pluggy` trực tiếp từ PyPI.

---

## 🏗️ Cấu Trúc Dự Án

```text
graphrag-pluggy-example/
├── pyproject.toml               # Cấu hình dependencies PyPI tiêu chuẩn (uv)
├── README.md                    # Hướng dẫn sử dụng & Live Demo Drop-in Plugin
├── docs/                        # Tài liệu đặc tả kỹ thuật (Spec)
│   └── spec-fastapi-graphrag-pluggy.md
├── examples/                    # 📦 THƯ MỤC CHỨA PLUGIN VÍ DỤ SẴN ĐỂ DEMO
│   └── censor_keyword.py        # File mẫu để bạn copy thử vào plugins/
├── plugins/                     # 📂 THƯ MỤC DROP-IN PLUGINS (Tự động quét & nạp)
│   ├── role_based_acl.py        # Plugin RBAC
│   ├── tenant_isolation_acl.py  # Plugin Tenant Isolation
│   └── pii_masking_acl.py       # Plugin PII Masking
├── app/
│   ├── main.py                  # Khởi tạo FastAPI app & lifespan quét plugins/
│   ├── core/
│   │   ├── config.py            # Cấu hình hệ thống
│   │   └── acl_specs.py         # Pluggy Hook Specifications (filter_input_docs, allow_node, filter_output_doc)
│   ├── schemas/
│   │   ├── plugin_schema.py     # Pydantic models cho Plugin APIs
│   │   └── pipeline_schema.py   # Pydantic models cho Extraction Pipeline & Context
│   ├── services/
│   │   ├── acl_manager.py       # DynamicACLManager tự động quét và quản lý thư mục plugins/
│   │   ├── pipeline_service.py  # Service thực thi luồng trích xuất tài liệu
│   │   └── pluggy_decorator.py  # Adapter cắm vào PipelineDecorator của GraphRAG
│   └── api/
│       └── v1/
│           ├── router.py        # Gộp router v1
│           ├── endpoints_plugins.py  # REST APIs kiểm tra và đồng bộ plugin
│           └── endpoints_pipeline.py # REST APIs thực thi pipeline trích xuất
└── tests/                       # Test suite (pytest)
    ├── conftest.py              # Fixtures reset trạng thái & TestClient
    ├── test_acl_manager.py      # Test unit cho ACL Manager & Plugins
    ├── test_pipeline_service.py # Test unit cho Pipeline Service
    ├── test_plugins_api.py      # Test API phát hiện và gỡ plugin động trong plugins/
    └── test_pipeline_api.py     # Test API các kịch bản phân quyền thực tế
```

---

## 🚀 Cài Đặt & Khởi Động

### 1. Yêu cầu môi trường

- Python 3.10 - 3.12
- Trình quản lý gói `uv`

### 2. Cài đặt dependencies

```bash
uv sync --extra dev
```

### 3. Khởi động Server

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- **Swagger UI Interactive Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🎬 KỊCH BẢN DEMO THỰC TẾ: COPY PLUGIN TỰ VIẾT VÀO `plugins/` (30 GIÂY)

Hệ thống đã chuẩn bị sẵn file mẫu tại **`examples/censor_keyword.py`**.

---

### Bước 1: Xem kết quả trích xuất lúc BÌNH THƯỜNG (Admin)

Gửi request trích xuất với tài liệu mẫu:

```bash
curl -s -X POST "http://localhost:8000/api/v1/pipeline/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "context": { "user_id": "admin_01", "tenant_id": "vn", "roles": ["admin"] },
    "documents": [
      {
        "doc_id": "doc_vn",
        "nodes": [
          { "node_id": "n1", "text": "Báo cáo doanh thu Q2", "metadata": {"classification": "PUBLIC", "tenant_id": "vn"} },
          { "node_id": "n2", "text": "Kế hoạch sáp nhập đối thủ", "metadata": {"classification": "RESTRICTED", "tenant_id": "vn"} }
        ]
      }
    ]
  }' | jq '.documents[0].nodes'
```

👉 **Kết quả**: Ra đủ **2 nodes** (`n1` và `n2`) với text gốc ban đầu.

---

### Bước 2: COPY file plugin vào thư mục `plugins/`

Chỉ cần chạy đúng 1 lệnh copy (hoặc kéo thả file trên giao diện OS):

```bash
cp examples/censor_keyword.py plugins/
```

---

### Bước 3: Gửi lại request ở Bước 1 $\rightarrow$ Tự động áp dụng ngay lập tức!

Gửi lại request trích xuất:

```bash
curl -s -X POST "http://localhost:8000/api/v1/pipeline/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "context": { "user_id": "admin_01", "tenant_id": "vn", "roles": ["admin"] },
    "documents": [
      {
        "doc_id": "doc_vn",
        "nodes": [
          { "node_id": "n1", "text": "Báo cáo doanh thu Q2", "metadata": {"classification": "PUBLIC", "tenant_id": "vn"} },
          { "node_id": "n2", "text": "Kế hoạch sáp nhập đối thủ", "metadata": {"classification": "RESTRICTED", "tenant_id": "vn"} }
        ]
      }
    ]
  }' | jq '.documents[0].nodes'
```

👉 **Kết quả quan sát thấy ngay**:

```json
[
	{
		"node_id": "n1",
		"text": "[VERIFIED_2026] Báo cáo doanh thu Q2",
		"metadata": {
			"classification": "PUBLIC",
			"tenant_id": "vn"
		}
	}
]
```

✅ **Minh chứng 1**: Node `n2` chứa từ "sáp nhập" **đã bị chặn hoàn toàn**.  
✅ **Minh chứng 2**: Node `n1` **tự động gắn watermark** `[VERIFIED_2026]`.

---

### Bước 4: Khi muốn gỡ bỏ Plugin

Chỉ cần xóa file khỏi thư mục `plugins/`:

```bash
rm plugins/censor_keyword.py
```

*(Chạy lại Bước 1 sẽ lập tức trở về kết quả gốc ban đầu mà không cần restart server)*.

---

## 📋 Bảng Tra Cứu API Quản Lý Plugin

| Method | Endpoint                            | Mô Tả                                          | Tham Số / Query                                                   |
|--------|-------------------------------------|------------------------------------------------|-------------------------------------------------------------------|
| `GET`  | `/api/v1/plugins`                   | Liệt kê plugins trong thư mục `plugins/`       | `active_only=true` (chỉ plugin đang bật), `sync=true` (auto-sync) |
| `POST` | `/api/v1/plugins/sync`              | Quét và đồng bộ lại thư mục `plugins/`         | Không cần payload                                                 |
| `POST` | `/api/v1/plugins/unregister/{name}` | Tắt tạm thời một plugin khỏi runtime           | Path param: `name`                                                |
| `POST` | `/api/v1/plugins/reset`             | Đồng bộ và khôi phục lại toàn bộ từ `plugins/` | Không cần payload                                                 |

---

## 🔍 Chạy Test Suite Tự Động

Chạy toàn bộ 14 automated tests:

```bash
uv run pytest -v
```

Kiểm tra định dạng và code quality:

```bash
uv run ruff check .
```
