# Kiến Trúc Tích Hợp Pluggy Vào GraphRAG-Toolkit (Zero Code Modification)

Tài liệu giải thích cơ chế kỹ thuật giúp mở rộng hệ thống plugin phân quyền (ACL) và xử lý dữ liệu cho **GraphRAG-Toolkit** mà **không cần chỉnh sửa bất kỳ dòng code nào** trong thư viện gốc.

---

## 1. Điểm Mở Rộng Chính Thức (Extension Point) Của GraphRAG-Toolkit

Trong mã nguồn chính thức của `graphrag_toolkit.lexical_graph.indexing.extract.extraction_pipeline`:
Lớp `ExtractionPipeline` được thiết kế có sẵn tham số `extraction_decorator` nhận vào một thể hiện của abstract base class `PipelineDecorator`.

```
                       [Tài Liệu Đầu Vào (SourceDocuments)]
                                        │
                                        ▼
             ┌─────────────────────────────────────────────────────┐
             │ 1. handle_input_docs(source_documents)              │ <── [EXT_POINT 1: INPUT FILTER]
             │    - Tiền xử lý, lọc quyền tài liệu & nodes         │
             └─────────────────────────────────────────────────────┘
                                        │ (Chỉ các node hợp lệ đi tiếp)
                                        ▼
             ┌─────────────────────────────────────────────────────┐
             │ 2. Core GraphRAG Processing Engine                  │
             │    - Chunking (SentenceSplitter / TokenSplitter)    │
             │    - LLM Proposition Extraction                     │
             │    - Entity / Relation / Topic Extraction           │
             └─────────────────────────────────────────────────────┘
                                        │
                                        ▼
             ┌─────────────────────────────────────────────────────┐
             │ 3. handle_output_doc(source_document)               │ <── [EXT_POINT 2: OUTPUT POST-PROCESS]
             │    - Hậu xử lý kết quả graph/nodes (PII masking)    │
             └─────────────────────────────────────────────────────┘
                                        │
                                        ▼
                       [Tài Liệu Đã Trích Xuất & Lưu Trữ]
```

### Interface `PipelineDecorator` Trong GraphRAG-Toolkit:
```python
# graphrag_toolkit/lexical_graph/indexing/extract/pipeline_decorator.py
class PipelineDecorator(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def handle_input_docs(self, docs: Iterable[SourceDocument]) -> Iterable[SourceDocument]:
        """Lọc và tiền xử lý documents trước khi chunking & gọi LLM"""
        pass

    @abc.abstractmethod
    def handle_output_doc(self, doc: SourceDocument) -> SourceDocument:
        """Hậu xử lý graph/nodes sau khi LLM trích xuất xong"""
        pass
```

---

## 2. Mô Hình Kết Nối (Adapter Pattern Với Pluggy)

Chúng ta triển khai `PluggyACLPipelineDecorator` để làm cầu nối (Bridge) giữa hai thế giới:
- **Phía GraphRAG**: Tuân thủ 100% contract của `PipelineDecorator`.
- **Phía Plugins**: Điều hướng sự kiện sang `Pluggy.PluginManager`.

```
[GraphRAG ExtractionPipeline]
             │
             │ (Gọi handle_input_docs / handle_output_doc)
             ▼
[PluggyACLPipelineDecorator] (Adapter)
             │
             │ (Gọi pm.hook.allow_node / filter_output_doc)
             ▼
[Pluggy PluginManager]
   ├── [role_based_acl.py]        (RBAC: Chặn node RESTRICTED)
   ├── [tenant_isolation_acl.py]  (Tenant Isolation: Chặn chéo tenant)
   ├── [pii_masking_acl.py]       (PII: Che email, SĐT)
   └── [custom_user_plugin.py]    (Plugin do khách hàng thả vào plugins/)
```

---

## 3. Quy Trình Vận Hành Với Dữ Liệu Thực Tế

1. **Khởi tạo Pipeline Thật**:
   ```python
   from graphrag_toolkit.lexical_graph.indexing.extract.extraction_pipeline import ExtractionPipeline
   from llama_index.core.node_parser import SentenceSplitter
   from app.services.pluggy_decorator import PluggyACLPipelineDecorator

   # Cắm decorator vào pipeline
   pipeline = ExtractionPipeline(
       components=[SentenceSplitter(chunk_size=500)],
       extraction_decorator=PluggyACLPipelineDecorator(context={"tenant_id": "vn", "roles": ["viewer"]}),
       num_workers=1
   )
   ```

2. **Thực thi trích xuất**:
   ```python
   extracted_docs = list(pipeline.extract(real_source_docs))
   ```

3. **Lợi ích**:
   - Tiết kiệm token LLM vì các tài liệu bị cấm bị chặn ngay tại `handle_input_docs` trước khi gửi lên AI.
   - Dữ liệu đầu ra được bảo vệ bởi các bộ lọc PII tại `handle_output_doc`.
   - Có thể thêm/bớt/sửa plugin trong thư mục `plugins/` bất cứ lúc nào mà không cần chạm vào `graphrag-toolkit`.
