from typing import Any

from app.core.acl_specs import hookimpl


class RoleBasedACLPlugin:
    """
    Plugin phân quyền theo vai trò (Role-Based Access Control - RBAC).

    Lý do tồn tại (Why it exists):
    - Đảm bảo các node dữ liệu có nhãn bảo mật (Classification) như RESTRICTED hoặc CONFIDENTIAL
      chỉ được phép trích xuất bởi người dùng có vai trò tương ứng (admin, security_officer, editor).
    """

    @hookimpl
    def allow_node(self, node: Any, context: dict[str, Any]) -> bool:
        roles = context.get("roles", [])
        metadata = getattr(node, "metadata", {}) or {}
        classification = str(metadata.get("classification", "PUBLIC")).upper()

        # Dữ liệu TUYỆT MẬT (RESTRICTED): chỉ Admin hoặc Security Officer được truy cập
        if classification == "RESTRICTED":
            if not any(r in roles for r in ["admin", "security_officer"]):
                return False

        # Dữ liệu NỘI BỘ (CONFIDENTIAL): yêu cầu ít nhất vai trò nội bộ hoặc biên tập viên
        if classification == "CONFIDENTIAL":
            if not any(r in roles for r in ["admin", "security_officer", "editor", "internal"]):
                return False

        return True
