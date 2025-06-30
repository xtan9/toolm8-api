import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.mark.unit
def test_root_endpoint():
    """Test the root endpoint returns correct message."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "ToolM8 Data Management API - AI Tools Scraping Service"
    }


@pytest.mark.unit
def test_health_check_endpoint():
    """Test the health check endpoint returns correct status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "toolm8-data-api"}