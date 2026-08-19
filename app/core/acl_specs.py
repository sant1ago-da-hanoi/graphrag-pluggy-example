from typing import Any

import pluggy

# Namespace định danh cho toàn bộ hệ thống plugin ACL của GraphRAG
HOOK_NAMESPACE = "graphrag_acl"

# HookspecMarker: Dùng để đánh dấu các phương thức định nghĩa giao diện (interface) hook
hookspec = pluggy.HookspecMarker(HOOK_NAMESPACE)

# HookimplMarker: Dùng để đánh dấu các hàm triển khai (implementation) trong từng plugin
hookimpl = pluggy.HookimplMarker(HOOK_NAMESPACE)


class ACLExtractHookSpec:
    """
    Tập hợp đặc tả (Hook Specifications) cho cơ chế phân quyền (ACL) trong Extraction Pipeline.

    Lý do tồn tại (Why it exists):
    - GraphRAG-Toolkit trích xuất thông tin qua nhiều bước (tiền xử lý -> chunking -> LLM extract -> tạo graph).
    - Cần các điểm chặn (hooks) chuẩn hóa để kiểm soát quyền truy cập tài liệu, từng node dữ liệu,
      và dữ liệu nhạy cảm đầu ra mà không phải sửa trực tiếp core codebase của GraphRAG.
    """

    @hookspec(firstresult=False)
    def filter_input_docs(self, docs: list[Any], context: dict[str, Any]) -> list[Any] | None:
        """
        Hook tiền xử lý danh sách tài liệu đầu vào trước khi đưa vào pipeline trích xuất.
        """
        pass

    @hookspec(firstresult=False)
    def allow_node(self, node: Any, context: dict[str, Any]) -> bool | None:
        """
        Hook kiểm tra quyền truy cập trên từng Node/Chunk dữ liệu (fine-grained access control).
        Sử dụng cơ chế phủ quyết (veto): Nếu BẤT KỲ plugin nào trả về False, node đó sẽ bị loại bỏ.
        """
        pass

    @hookspec(firstresult=False)
    def filter_output_doc(self, doc: Any, context: dict[str, Any]) -> Any | None:
        """
        Hook hậu xử lý trên tài liệu/graph sau khi đã trích xuất xong từ LLM (ví dụ: PII masking).
        """
        pass
