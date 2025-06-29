import asyncio
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import db_connection
from app.database.service import db_service


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def mock_db_pool():
    """Mock database pool for testing"""
    pool = AsyncMock()
    conn = AsyncMock()
    pool.acquire.return_value.__aenter__.return_value = conn
    pool.acquire.return_value.__aexit__.return_value = None
    return pool, conn


@pytest_asyncio.fixture
async def mock_db_connection(mock_db_pool):
    """Mock database connection for testing"""
    pool, conn = mock_db_pool
    original_get_pool = db_connection.get_pool
    db_connection.get_pool = AsyncMock(return_value=pool)
    
    yield pool, conn
    
    db_connection.get_pool = original_get_pool


@pytest.fixture
def sample_category_data():
    """Sample category data for testing"""
    return {
        "name": "Test Category",
        "slug": "test-category",
        "description": "A test category",
        "display_order": 1,
        "is_featured": True
    }


@pytest.fixture
def sample_tool_data():
    """Sample tool data for testing"""
    return {
        "name": "Test AI Tool",
        "slug": "test-ai-tool",
        "description": "A test AI tool for testing purposes",
        "website_url": "https://example.com",
        "pricing_type": "freemium",
        "has_free_trial": True,
        "category_id": 1,
        "tags": ["ai", "test", "tool"],
        "features": ["API", "Real-time"],
        "quality_score": 8,
        "source": "test"
    }


@pytest.fixture
def mock_aiohttp_session():
    """Mock aiohttp session for scraper testing"""
    session = AsyncMock()
    response = AsyncMock()
    response.status = 200
    response.text = AsyncMock(return_value="<html><h1>Test Tool</h1></html>")
    session.get.return_value.__aenter__.return_value = response
    session.get.return_value.__aexit__.return_value = None
    return session


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()