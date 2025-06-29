import pytest
from unittest.mock import AsyncMock, patch
from app.database.service import DatabaseService
from app.models import CategoryCreate, ToolCreate, Category, Tool


class TestDatabaseService:
    
    @pytest.mark.asyncio
    async def test_insert_category_success(self, mock_db_connection, sample_category_data):
        """Test successful category insertion"""
        pool, conn = mock_db_connection
        
        # Mock database response
        mock_row = {
            "id": 1,
            "name": "Test Category",
            "slug": "test-category",
            "description": "A test category",
            "display_order": 1,
            "is_featured": True,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
        conn.fetchrow.return_value = mock_row
        
        db_service = DatabaseService()
        category = CategoryCreate(**sample_category_data)
        result = await db_service.insert_category(category)
        
        assert result is not None
        assert result.name == "Test Category"
        assert result.id == 1
        conn.fetchrow.assert_called_once()

    @pytest.mark.asyncio
    async def test_insert_category_failure(self, mock_db_connection, sample_category_data):
        """Test category insertion failure"""
        pool, conn = mock_db_connection
        conn.fetchrow.side_effect = Exception("Database error")
        
        db_service = DatabaseService()
        category = CategoryCreate(**sample_category_data)
        result = await db_service.insert_category(category)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_insert_tool_success(self, mock_db_connection, sample_tool_data):
        """Test successful tool insertion"""
        pool, conn = mock_db_connection
        
        mock_row = {
            "id": 1,
            "name": "Test AI Tool",
            "slug": "test-ai-tool",
            "description": "A test AI tool",
            "website_url": "https://example.com",
            "logo_url": None,
            "pricing_type": "freemium",
            "price_range": None,
            "has_free_trial": True,
            "category_id": 1,
            "tags": ["ai", "test"],
            "features": ["API"],
            "quality_score": 8,
            "popularity_score": 0,
            "is_featured": False,
            "click_count": 0,
            "source": "test",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
        conn.fetchrow.return_value = mock_row
        
        db_service = DatabaseService()
        tool = ToolCreate(**sample_tool_data)
        result = await db_service.insert_tool(tool)
        
        assert result is not None
        assert result.name == "Test AI Tool"
        assert result.id == 1

    @pytest.mark.asyncio
    async def test_bulk_insert_tools_success(self, mock_db_connection):
        """Test bulk tool insertion"""
        pool, conn = mock_db_connection
        conn.execute.return_value = "INSERT 0 1"  # Successful insert
        
        tools = [
            ToolCreate(name="Tool 1", slug="tool-1"),
            ToolCreate(name="Tool 2", slug="tool-2"),
            ToolCreate(name="Tool 3", slug="tool-3")
        ]
        
        db_service = DatabaseService()
        result = await db_service.bulk_insert_tools(tools)
        
        assert result == 3
        assert conn.execute.call_count == 3

    @pytest.mark.asyncio
    async def test_bulk_insert_tools_partial_failure(self, mock_db_connection):
        """Test bulk insert with some failures"""
        pool, conn = mock_db_connection
        
        # First two succeed, third fails
        conn.execute.side_effect = [
            "INSERT 0 1",
            "INSERT 0 1", 
            Exception("Duplicate key")
        ]
        
        tools = [
            ToolCreate(name="Tool 1", slug="tool-1"),
            ToolCreate(name="Tool 2", slug="tool-2"),
            ToolCreate(name="Tool 3", slug="tool-3")
        ]
        
        db_service = DatabaseService()
        result = await db_service.bulk_insert_tools(tools)
        
        assert result == 2  # Only 2 successful

    @pytest.mark.asyncio
    async def test_check_duplicate_tool_by_name(self, mock_db_connection):
        """Test duplicate detection by name"""
        pool, conn = mock_db_connection
        conn.fetchval.return_value = True
        
        db_service = DatabaseService()
        result = await db_service.check_duplicate_tool(name="Existing Tool")
        
        assert result is True
        conn.fetchval.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_duplicate_tool_by_url(self, mock_db_connection):
        """Test duplicate detection by URL"""
        pool, conn = mock_db_connection
        conn.fetchval.return_value = False
        
        db_service = DatabaseService()
        result = await db_service.check_duplicate_tool(website_url="https://new-tool.com")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_check_duplicate_tool_no_params(self, mock_db_connection):
        """Test duplicate check with no parameters"""
        db_service = DatabaseService()
        result = await db_service.check_duplicate_tool()
        
        assert result is False

    @pytest.mark.asyncio
    async def test_get_all_categories(self, mock_db_connection):
        """Test getting all categories"""
        pool, conn = mock_db_connection
        
        mock_rows = [
            {
                "id": 1,
                "name": "Category 1",
                "slug": "category-1",
                "description": "First category",
                "display_order": 1,
                "is_featured": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            },
            {
                "id": 2,
                "name": "Category 2", 
                "slug": "category-2",
                "description": "Second category",
                "display_order": 2,
                "is_featured": False,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        ]
        conn.fetch.return_value = mock_rows
        
        db_service = DatabaseService()
        result = await db_service.get_all_categories()
        
        assert len(result) == 2
        assert result[0].name == "Category 1"
        assert result[1].name == "Category 2"

    @pytest.mark.asyncio
    async def test_find_category_by_name(self, mock_db_connection):
        """Test finding category by name"""
        pool, conn = mock_db_connection
        
        mock_row = {
            "id": 1,
            "name": "Found Category",
            "slug": "found-category",
            "description": "A found category",
            "display_order": 1,
            "is_featured": True,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
        conn.fetchrow.return_value = mock_row
        
        db_service = DatabaseService()
        result = await db_service.find_category_by_name("Found Category")
        
        assert result is not None
        assert result.name == "Found Category"

    @pytest.mark.asyncio
    async def test_find_category_by_name_not_found(self, mock_db_connection):
        """Test finding non-existent category"""
        pool, conn = mock_db_connection
        conn.fetchrow.return_value = None
        
        db_service = DatabaseService()
        result = await db_service.find_category_by_name("Non-existent")
        
        assert result is None

    def test_generate_slug(self):
        """Test slug generation"""
        db_service = DatabaseService()
        
        assert db_service.generate_slug("Test Tool Name") == "test-tool-name"
        assert db_service.generate_slug("AI & Machine Learning") == "ai-machine-learning"
        assert db_service.generate_slug("Special@Characters#Here!") == "specialcharactershere"

    @pytest.mark.asyncio
    async def test_get_tools_by_category(self, mock_db_connection):
        """Test getting tools by category"""
        pool, conn = mock_db_connection
        
        mock_rows = [
            {
                "id": 1,
                "name": "Tool 1",
                "slug": "tool-1",
                "description": "First tool",
                "website_url": "https://tool1.com",
                "logo_url": None,
                "pricing_type": "free",
                "price_range": None,
                "has_free_trial": False,
                "category_id": 1,
                "tags": ["ai"],
                "features": ["API"],
                "quality_score": 7,
                "popularity_score": 10,
                "is_featured": True,
                "click_count": 0,
                "source": "test",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        ]
        conn.fetch.return_value = mock_rows
        
        db_service = DatabaseService()
        result = await db_service.get_tools_by_category(1, limit=10, offset=0)
        
        assert len(result) == 1
        assert result[0].name == "Tool 1"
        assert result[0].category_id == 1