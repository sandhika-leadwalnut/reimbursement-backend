import pytest
from fastapi.testclient import TestClient
from main import app
from unittest.mock import Mock, patch

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_supabase():
    with patch("core.supabase.create_client") as mock:
        yield mock

@pytest.fixture
def mock_zoho():
    with patch("services.zoho.httpx.AsyncClient") as mock:
        yield mock
