import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app


class TestAPIEndpoints:
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        assert "ToolM8 Data Management API" in response.json()["message"]

    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "toolm8-data-api"


    @patch('app.main.run_scraper_task')
    def test_scrape_tools_endpoint(self, mock_scraper, client):
        """Test scrape tools endpoint"""
        response = client.post("/admin/scrape-tools?max_pages=5")
        assert response.status_code == 200
        data = response.json()
        assert "Scraping started for 5 pages" in data["message"]

    @patch('app.main.run_scraper_task')
    def test_scrape_tools_endpoint_default_pages(self, mock_scraper, client):
        """Test scrape tools endpoint with default pages"""
        response = client.post("/admin/scrape-tools")
        assert response.status_code == 200
        data = response.json()
        assert "Scraping started for 10 pages" in data["message"]

    @patch('app.database.connection.db_connection.get_pool')
    async def test_stats_endpoint(self, mock_get_pool, client):
        """Test database stats endpoint"""
        # Mock the database connection and queries
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_pool.acquire.return_value.__aexit__.return_value = None
        mock_get_pool.return_value = mock_pool
        
        # Mock query results
        mock_conn.fetchval.side_effect = [10, 500, 25]  # categories, tools, recent_tools
        mock_conn.fetch.return_value = [
            {"source": "theresanaiforthat", "count": 450},
            {"source": "manual", "count": 50}
        ]
        
        response = client.get("/admin/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["categories_count"] == 10
        assert data["tools_count"] == 500
        assert data["recent_tools_24h"] == 25
        assert len(data["sources"]) == 2

    @patch('app.database.connection.db_connection.get_pool')
    async def test_clear_tools_all(self, mock_get_pool, client):
        """Test clearing all tools"""
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_pool.acquire.return_value.__aexit__.return_value = None
        mock_get_pool.return_value = mock_pool
        
        mock_conn.execute.return_value = "DELETE 500"
        
        response = client.delete("/admin/clear-tools")
        assert response.status_code == 200
        data = response.json()
        assert "Cleared all tools" in data["message"]
        assert data["rows_deleted"] == 500

    @patch('app.database.connection.db_connection.get_pool') 
    async def test_clear_tools_by_source(self, mock_get_pool, client):
        """Test clearing tools by source"""
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_pool.acquire.return_value.__aexit__.return_value = None
        mock_get_pool.return_value = mock_pool
        
        mock_conn.execute.return_value = "DELETE 300"
        
        response = client.delete("/admin/clear-tools?source=theresanaiforthat")
        assert response.status_code == 200
        data = response.json()
        assert "Cleared tools from source: theresanaiforthat" in data["message"]
        assert data["rows_deleted"] == 300


    @patch('app.main.run_scraper_task')
    def test_scrape_tools_endpoint_error(self, mock_scraper, client):
        """Test scrape tools endpoint with error"""
        mock_scraper.side_effect = Exception("Scraping failed")
        
        response = client.post("/admin/scrape-tools")
        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Failed to start scraping"

    @patch('app.database.connection.db_connection.get_pool')
    async def test_stats_endpoint_error(self, mock_get_pool, client):
        """Test stats endpoint with database error"""
        mock_get_pool.side_effect = Exception("Database connection failed")
        
        response = client.get("/admin/stats")
        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Failed to get stats"

    @patch('app.database.connection.db_connection.get_pool')
    async def test_clear_tools_error(self, mock_get_pool, client):
        """Test clear tools endpoint with database error"""
        mock_get_pool.side_effect = Exception("Database connection failed")
        
        response = client.delete("/admin/clear-tools")
        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Failed to clear tools"


class TestAPIErrorHandling:
    
    def test_404_endpoint(self, client):
        """Test non-existent endpoint returns 404"""
        response = client.get("/non-existent")
        assert response.status_code == 404

    def test_invalid_method(self, client):
        """Test invalid HTTP method"""
        response = client.put("/admin/stats")  # Use existing endpoint
        assert response.status_code == 405

    def test_invalid_query_params(self, client):
        """Test invalid query parameters"""
        response = client.post("/admin/scrape-tools?max_pages=invalid")
        assert response.status_code == 422  # Unprocessable Entity