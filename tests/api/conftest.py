# tests/api/conftest.py
import pytest
from fastapi.testclient import TestClient
from typing import Generator

# Import from parent conftest or create specific API fixtures
from myapp.main import app


@pytest.fixture(scope="function")
def api_client() -> Generator:
    """Create test client for API testing"""
    with TestClient(app) as test_client:
        yield test_client


# You can also override or add API-specific fixtures here
@pytest.fixture
def api_test_user_data():
    """Test user data for API tests"""
    return {
        "email": "apitest@example.com",
        "username": "apitestuser",
        "password": "ApiTest123!"
    }