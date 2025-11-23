"""Simple test to verify test infrastructure works."""

import pytest
from fastapi.testclient import TestClient
from auth_module.main import app

def test_simple():
    """Simple test that doesn't require database."""
    client = TestClient(app)
    response = client.get("/health")
    # This might not exist, but at least we can see if the test runs
    assert response.status_code in [200, 404]

