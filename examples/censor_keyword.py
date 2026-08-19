from app.core.acl_specs import hookimpl


class CensorKeywordPlugin:
    """
    Plugin ví dụ do khách hàng tự phát triển:
    1. allow_node: Chặn bất kỳ đoạn văn nào chứa từ khóa nhạy cảm 'sáp nhập'.
    2. filter_output_doc: Tự động chèn tiền tố xác thực '[VERIFIED_2026]' vào đầu mỗi đoạn văn bản xuất ra.
    """

    @hookimpl
    def allow_node(self, node, context: dict) -> bool:
        text = getattr(node, "text", "").lower()
        # Chặn nếu phát hiện từ khóa nhạy cảm
        if "sáp nhập" in text:
            return False
        return True

    @hookimpl
    def filter_output_doc(self, doc, context: dict):
        # Đính kèm watermark vào tất cả các node đầu ra
        for node in getattr(doc, "nodes", []):
            current_text = getattr(node, "text", "")
            node.text = f"[VERIFIED_2026] {current_text}"
        return doc
