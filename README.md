# FastAPI Dynamic ACL Plugin Showcase for GraphRAG-Toolkit

Ứng dụng REST API xây dựng bằng **FastAPI** và **Pluggy** nhằm trình diễn và quản lý cơ chế **Dynamic Drop-in Plugins**
tích hợp trực tiếp vào **Extraction Pipeline THỰC TẾ** của **GraphRAG-Toolkit** (`graphrag-lexical-graph`).

---

## 🎯 Giá Trị Cốt Lõi (Core Value Proposition)

> **"Can thiệp và kiểm soát toàn bộ luồng trích xuất của GraphRAG-Toolkit mà KHÔNG cần sửa bất kỳ dòng code nào của thư
viện. Khách hàng chỉ cần thả file Python `.py` vào thư mục `plugins/` $\rightarrow$ Hệ thống tự động nạp và áp dụng ngay
lập tức (Zero Restart)."**

👉 *Xem chi tiết tài liệu kiến trúc kỹ thuật tại: [
`docs/architecture-graphrag-extension-point.md`](docs/architecture-graphrag-extension-point.md)*

---

## 📐 Kiến Trúc Luồng Đăng Ký & Thực Thi Plugin

```text
====================================================================================================
               LUỒNG HOẠT ĐỘNG: DROP-IN PLUGIN -> DYNAMIC REGISTER -> GRAPHRAG
====================================================================================================

[ 1. HÀNH ĐỘNG CỦA DEVELOPER / KHÁCH HÀNG ]
   │
   │  Viết file: "censor_keyword.py"
   │  (Chứa class có hàm gắn decorator @hookimpl)
   │
   ▼
[ 2. THẢ FILE VÀO THƯ MỤC "plugins/" ]
   │  
   │  cp censor_keyword.py plugins/
   │
   ▼
[ 3. DYNAMIC ACL MANAGER (app/services/acl_manager.py) ]
   │
   ├──► Quét thư mục: Path("plugins/").glob("*.py")
   │
   ├──► Đọc & Compile mã nguồn (Zero Bytecode Caching):
   │       source_code = file_path.read_text()
   │       code = compile(source_code, path, 'exec')
   │       exec(code, module.__dict__)
   │
   ├──► Tự động phát hiện Plugin Class (Reflection / Inspection):
   │       Tìm thấy: class CensorKeywordPlugin
   │       Tạo instance: plugin_instance = CensorKeywordPlugin()
   │
   ▼
[ 4. NẠP VÀO PLUGGY ENGINE (RAM Memory - Zero Downtime) ]
   │
   │  pm.register(plugin_instance, name="censor_keyword")
   │  
   ├──► Cập nhật bảng điều phối Hook:
   │       ┌─────────────────────────────────────────────────────────────┐
   │       │ Pluggy Hook Registry ("graphrag_acl")                       │
   │       │  ├── allow_node:                                            │
   │       │  │    [RoleBasedACL, TenantIsolationACL, CensorKeyword] <───┤ (Thêm mới vào RAM)
   │       │  └── filter_output_doc:                                     │
   │       │       [PIIMaskingACL, CensorKeyword]                    <───┤ (Thêm mới vào RAM)
   │       └─────────────────────────────────────────────────────────────┘
   │
   ▼
[ 5. THỰC THI QUA GRAPHRAG EXTRACTION PIPELINE ]
   │
   │  Client gọi: POST /api/v1/pipeline/extract
   │
   ├──► [Điểm Chặn 1: Tiền Xử Lý (Dòng 444 trong GraphRAG ExtractionPipeline)]
   │       │
   │       ▼
   │    ExtractionPipeline.handle_input_docs(docs)
   │       │
   │       ▼
   │    PluggyACLPipelineDecorator (Adapter)
   │       │
   │       └──► pm.hook.allow_node(node, context)
   │               ├── RoleBasedACL        ──► True
   │               ├── TenantIsolationACL  ──► True
   │               └── CensorKeywordPlugin ──► FALSE (Phát hiện từ "sáp nhập")
   │               
   │               ==> [VETO RULE: Bị loại bỏ ngay trước khi chunking / LLM]
   │
   └──► [Điểm Chặn 2: Hậu Xử Lý (Dòng 489 trong GraphRAG ExtractionPipeline)]
           │
           ▼
        ExtractionPipeline.handle_output_doc(doc)
           │
           ▼
        PluggyACLPipelineDecorator (Adapter)
           │
           └──► pm.hook.filter_output_doc(doc, context)
                   ├── PIIMaskingACL       ──► [REDACTED_EMAIL]
                   └── CensorKeywordPlugin ──► Chèn [VERIFIED_2026] vào text
                   
                   ==> [Trả kết quả an toàn & đã enrich về cho Client]
====================================================================================================
```

---

## 🌟 Tính Năng Nổi Bật

1. **⚡ Thực Thi Qua `ExtractionPipeline` Thật Của GraphRAG**:
    - Sử dụng trực tiếp các class chuẩn `ExtractionPipeline`, `SourceDocument` từ package `graphrag-lexical-graph`.
    - Kết nối qua abstract class `PipelineDecorator` chính thức của GraphRAG.
2. **📂 Drop-in Plugin Architecture (Zero Config & Zero Downtime)**:
    - Thư mục `plugins/` đóng vai trò là kho plugin sống.
    - Thả file mới vào `plugins/` $\rightarrow$ Hệ thống **tự động nạp (Auto-Discover & Load)**.
    - Sửa code trong file $\rightarrow$ Hệ thống **tự động Hot-Reload version mới**.
    - Xóa file khỏi `plugins/` $\rightarrow$ Hệ thống **tự động gỡ bỏ (Unregister)**.
3. **🛡️ Kiểm Soát Truy Cập Đa Tầng (Multi-layer ACL)**:
    - **Role-Based Access Control (RBAC)**: Lọc các Node có nhãn bảo mật `RESTRICTED` hoặc `CONFIDENTIAL` theo danh sách
      `roles` của người dùng.
    - **Tenant Isolation**: Ngăn chặn rò rỉ dữ liệu giữa các tổ chức (`tenant_id`), bảo vệ kiến trúc SaaS.
    - **PII Masking**: Tự động che giấu số điện thoại (`[REDACTED_PHONE]`) và email (`[REDACTED_EMAIL]`) ở bước xuất kết
      quả đối với người dùng thông thường.

---

## 🏗️ Cấu Trúc Dự Án

```text
graphrag-pluggy-example/
├── pyproject.toml               # Cấu hình dependencies PyPI tiêu chuẩn (uv)
├── README.md                    # Hướng dẫn sử dụng & Live Demo Drop-in Plugin
├── docs/                        # Tài liệu đặc tả kỹ thuật & Kiến trúc
│   ├── spec-fastapi-graphrag-pluggy.md
│   └── architecture-graphrag-extension-point.md # Tài liệu chứng minh Extension Point
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
│   │   ├── pipeline_service.py  # Service gọi ExtractionPipeline thật của GraphRAG
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

## 📋 Danh Sách Đầy Đủ Các API

| Nhóm         | Method | Endpoint                            | Mô Tả                                           | Tham Số / Body                              |
|--------------|--------|-------------------------------------|-------------------------------------------------|---------------------------------------------|
| **Pipeline** | `POST` | `/api/v1/pipeline/extract`          | Trích xuất tài liệu qua ExtractionPipeline thật | `ExtractRequest` (context + documents)      |
| **Pipeline** | `GET`  | `/api/v1/pipeline/sample-docs`      | Lấy dữ liệu tài liệu mẫu để test nhanh          | Không cần param                             |
| **Plugins**  | `GET`  | `/api/v1/plugins`                   | Liệt kê danh sách plugin trong `plugins/`       | `active_only=true/false`, `sync=true/false` |
| **Plugins**  | `POST` | `/api/v1/plugins/sync`              | Đồng bộ lại toàn bộ thư mục `plugins/`          | Không cần body                              |
| **Plugins**  | `POST` | `/api/v1/plugins/unregister/{name}` | Tắt tạm thời 1 plugin tại runtime               | Path param: `name`                          |
| **Plugins**  | `POST` | `/api/v1/plugins/reset`             | Khôi phục trạng thái từ `plugins/`              | Không cần body                              |

---

## 🎬 KỊCH BẢN LIVE DEMO: DROP-IN PLUGIN VÀO `plugins/` (30 GIÂY)

Hệ thống đã chuẩn bị sẵn file mẫu tại **`examples/censor_keyword.py`** với logic:

- `allow_node`: Chặn bất kỳ node nào có từ khóa nhạy cảm `"sáp nhập"`.
- `filter_output_doc`: Chèn tiền tố `[VERIFIED_2026]` vào text xuất ra.

---

### Bước 1: Gọi API Extract lúc BÌNH THƯỜNG (Admin)

Gửi request trích xuất:

```bash
curl -X POST "http://localhost:8000/api/v1/pipeline/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "context": {
      "user_id": "admin_01",
      "tenant_id": "vn",
      "roles": ["admin"]
    },
    "documents": [
      {
        "doc_id": "doc_vn",
        "nodes": [
          {
            "node_id": "n1",
            "text": "Báo cáo doanh thu Q2 tăng trưởng tốt.",
            "metadata": {"classification": "PUBLIC", "tenant_id": "vn"}
          },
          {
            "node_id": "n2",
            "text": "Kế hoạch sáp nhập đối thủ cạnh tranh vào cuối năm.",
            "metadata": {"classification": "RESTRICTED", "tenant_id": "vn"}
          }
        ]
      }
    ]
  }'
```

👉 **Kết quả trả về**:

```json
{
	"total_input_docs": 1,
	"total_input_nodes": 2,
	"total_output_docs": 1,
	"total_output_nodes": 2,
	"documents": [
		{
			"doc_id": "doc_vn",
			"nodes": [
				{
					"node_id": "n1",
					"text": "Báo cáo doanh thu Q2 tăng trưởng tốt.",
					"metadata": {
						"classification": "PUBLIC",
						"tenant_id": "vn"
					}
				},
				{
					"node_id": "n2",
					"text": "Kế hoạch sáp nhập đối thủ cạnh tranh vào cuối năm.",
					"metadata": {
						"classification": "RESTRICTED",
						"tenant_id": "vn"
					}
				}
			]
		}
	]
}
```

*(Admin xem được đầy đủ cả 2 nodes `n1` và `n2`)*.

---

### Bước 2: THẢ FILE PLUGIN VÀO THƯ MỤC `plugins/`

Chạy lệnh copy file mẫu vào thư mục `plugins/`:

```bash
cp examples/censor_keyword.py plugins/
```

---

### Bước 3: GỬI LẠI ĐÚNG REQUEST Ở BƯỚC 1 $\rightarrow$ KẾT QUẢ THAY ĐỔI NGAY

Gửi lại đúng lệnh `curl` ở Bước 1:

```bash
curl -X POST "http://localhost:8000/api/v1/pipeline/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "context": {
      "user_id": "admin_01",
      "tenant_id": "vn",
      "roles": ["admin"]
    },
    "documents": [
      {
        "doc_id": "doc_vn",
        "nodes": [
          {
            "node_id": "n1",
            "text": "Báo cáo doanh thu Q2 tăng trưởng tốt.",
            "metadata": {"classification": "PUBLIC", "tenant_id": "vn"}
          },
          {
            "node_id": "n2",
            "text": "Kế hoạch sáp nhập đối thủ cạnh tranh vào cuối năm.",
            "metadata": {"classification": "RESTRICTED", "tenant_id": "vn"}
          }
        ]
      }
    ]
  }'
```

👉 **Kết quả trả về ngay lập tức**:

```json
{
	"total_input_docs": 1,
	"total_input_nodes": 2,
	"total_output_docs": 1,
	"total_output_nodes": 1,
	"documents": [
		{
			"doc_id": "doc_vn",
			"nodes": [
				{
					"node_id": "n1",
					"text": "[VERIFIED_2026] Báo cáo doanh thu Q2 tăng trưởng tốt.",
					"metadata": {
						"classification": "PUBLIC",
						"tenant_id": "vn"
					}
				}
			]
		}
	]
}
```

✅ **Minh chứng 1**: Node `n2` chứa từ `"sáp nhập"` **đã bị lọc bỏ hoàn toàn** (`total_output_nodes: 1`).  
✅ **Minh chứng 2**: Node `n1` **tự động được chèn tiền tố** `[VERIFIED_2026]` vào văn bản.

---

### Bước 4: GỠ BỎ PLUGIN

Xóa file khỏi thư mục `plugins/`:

```bash
rm plugins/censor_keyword.py
```

*(Gửi lại request ở Bước 1 $\rightarrow$ Kết quả lập tức trở về 2 nodes ban đầu mà không cần restart server!)*

---

## 🔍 Chạy Test Suite Tự Động

Chạy toàn bộ 14 automated tests:

```bash
uv run pytest -v
```

Kiểm tra code quality:

```bash
uv run ruff check .
```
