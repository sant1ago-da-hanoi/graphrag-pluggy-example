import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.acl_manager import get_acl_manager


@pytest.fixture(autouse=True)
def reset_acl_state():
    """Reset ACL manager state before and after each test"""
    acl_mgr = get_acl_manager()
    acl_mgr.reset()
    yield
    acl_mgr.reset()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
