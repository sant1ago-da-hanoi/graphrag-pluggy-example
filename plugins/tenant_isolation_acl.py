from typing import Any

from app.core.acl_specs import hookimpl


class TenantIsolationACLPlugin:
    """
    Plugin cách ly dữ liệu đa người thuê (Multi-tenant Data Isolation).

    Lý do tồn tại (Why it exists):
    - Đảm bảo không xảy ra hiện tượng rò rỉ dữ liệu chéo giữa các tenant (Cross-tenant data leakage).
    - Ngăn chặn người dùng tenant A đọc dữ liệu của tenant B (trừ superadmin hoặc global data).
    """

    @hookimpl
    def allow_node(self, node: Any, context: dict[str, Any]) -> bool:
        roles = context.get("roles", [])
        if "superadmin" in roles:
            return True

        user_tenant = context.get("tenant_id")
        metadata = getattr(node, "metadata", {}) or {}
        node_tenant = metadata.get("tenant_id")

        # Nếu node có gắn nhãn tenant cụ thể (không phải global)
        if node_tenant and node_tenant != "global":
            # Từ chối nếu user không có tenant_id hoặc tenant_id không trùng khớp
            if not user_tenant or user_tenant != node_tenant:
                return False

        return True
