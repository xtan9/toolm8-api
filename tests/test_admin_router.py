import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.mark.unit
def test_admin_stats_endpoint():
    """Test the admin stats endpoint returns correct message."""
    response = client.get("/admin/stats")
    assert response.status_code == 200
    assert response.json() == {"message": "Admin stats endpoint - implement as needed"}