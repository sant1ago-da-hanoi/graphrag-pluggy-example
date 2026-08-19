from dataclasses import dataclass, field
from typing import Any

from app.services.acl_manager import DynamicACLManager


@dataclass
class MockNode:
    node_id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MockDoc:
    nodes: list[MockNode] = field(default_factory=list)


def test_acl_manager_lifecycle():
    manager = DynamicACLManager(plugins_dir="plugins")
    manager.scan_and_load_plugins()

    plugins = manager.list_plugins()
    assert len(plugins) == 3
    assert any(p["name"] == "role_based_acl" for p in plugins)
    assert any(p["name"] == "tenant_isolation_acl" for p in plugins)
    assert any(p["name"] == "pii_masking_acl" for p in plugins)

    # Test RBAC
    public_node = MockNode("n1", "Hello public", {"classification": "PUBLIC"})
    restricted_node = MockNode("n2", "Secret", {"classification": "RESTRICTED"})

    user_context = {"roles": ["viewer"], "tenant_id": "vn"}
    verdicts = manager.pm.hook.allow_node(node=public_node, context=user_context)
    assert False not in verdicts

    verdicts = manager.pm.hook.allow_node(node=restricted_node, context=user_context)
    assert False in verdicts  # Denied by RBAC

    admin_context = {"roles": ["admin"], "tenant_id": "vn"}
    verdicts = manager.pm.hook.allow_node(node=restricted_node, context=admin_context)
    assert False not in verdicts  # Allowed

    # Test Tenant Isolation
    vn_node = MockNode("n3", "VN data", {"tenant_id": "vn"})
    us_context = {"roles": ["viewer"], "tenant_id": "us"}
    verdicts = manager.pm.hook.allow_node(node=vn_node, context=us_context)
    assert False in verdicts  # Denied by TenantIsolation

    # Test PII Masking
    pii_doc = MockDoc(nodes=[MockNode("n4", "Contact: test@gmail.com and 0901234567")])
    res = manager.pm.hook.filter_output_doc(doc=pii_doc, context={"roles": ["viewer"]})
    masked_doc = res[-1]
    assert "[REDACTED_EMAIL]" in masked_doc.nodes[0].text
    assert "[REDACTED_PHONE]" in masked_doc.nodes[0].text
