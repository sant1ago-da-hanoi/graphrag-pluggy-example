import re
from typing import Any

from app.core.acl_specs import hookimpl


class PIIMaskingACLPlugin:
    """
    Plugin che giấu thông tin định danh cá nhân (PII Masking / Anonymization).

    Lý do tồn tại (Why it exists):
    - Tự động ẩn số điện thoại ([REDACTED_PHONE]) và email ([REDACTED_EMAIL])
      đối với người dùng không có quyền `can_view_pii`.
    """

    @hookimpl
    def filter_output_doc(self, doc: Any, context: dict[str, Any]) -> Any:
        permissions = context.get("permissions", [])
        roles = context.get("roles", [])

        # Nếu người dùng có quyền xem PII hoặc là admin/security_officer, không cần che
        if "can_view_pii" in permissions or "admin" in roles:
            return doc

        phone_regex = re.compile(r"\+?[\d\(\)][\d\s\-\.\(\)]{7,}\d")
        email_regex = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

        nodes = getattr(doc, "nodes", []) or []
        for node in nodes:
            text = getattr(node, "text", "")
            if text:
                masked_text = phone_regex.sub("[REDACTED_PHONE]", text)
                masked_text = email_regex.sub("[REDACTED_EMAIL]", masked_text)
                node.text = masked_text

        return doc
