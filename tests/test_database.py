import pytest
from unittest.mock import Mock, patch
from app.database.connection import DatabaseConnection, db_connection
from app.database.service import DatabaseService, db_service
from app.models import Tool, ToolCreate


class TestDatabaseConnection:
    def test_init(self):
        """Test DatabaseConnection initialization"""
        conn = DatabaseConnection()
        assert conn._client is None

    @patch('app.database.connection.create_client')
    def test_get_client_creates_new_client(self, mock_create_client):
        """Test that get_client creates a new Supabase client"""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        conn = DatabaseConnection()
        client = conn.get_client()
        
        assert client == mock_client
        assert conn._client == mock_client
        mock_create_client.assert_called_once()

    @patch('app.database.connection.create_client')
    def test_get_client_reuses_existing_client(self, mock_create_client):
        """Test that get_client reuses existing client"""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        conn = DatabaseConnection()
        client1 = conn.get_client()
        client2 = conn.get_client()
        
        assert client1 == client2 == mock_client
        mock_create_client.assert_called_once()

    @patch('app.database.connection.create_client')
    def test_get_client_handles_error(self, mock_create_client):
        """Test that get_client handles creation errors"""
        mock_create_client.side_effect = Exception("Connection failed")
        
        conn = DatabaseConnection()
        
        with pytest.raises(Exception, match="Connection failed"):
            conn.get_client()


class TestDatabaseService:
    def setup_method(self):
        """Setup for each test method"""
        self.service = DatabaseService()
        self.mock_client = Mock()

    @patch.object(db_connection, 'get_client')
    def test_insert_tool_success(self, mock_get_client):
        """Test successful tool insertion"""
        mock_get_client.return_value = self.mock_client
        
        mock_response = Mock()
        mock_response.data = [{
            'id': 1, 'name': 'Test Tool', 'slug': 'test-tool',
            'description': 'Test tool desc', 'website_url': 'https://test.com',
            'logo_url': None, 'pricing_type': 'free', 'price_range': None,
            'has_free_trial': False, 'tags': ['test', 'ai'],
            'features': ['feature1'], 'quality_score': 8, 'popularity_score': 0,
            'is_featured': False, 'click_count': 0, 'source': 'test',
            'created_at': '2023-01-01T00:00:00Z', 'updated_at': '2023-01-01T00:00:00Z'
        }]
        
        self.mock_client.table.return_value.insert.return_value.execute.return_value = mock_response
        
        tool_data = ToolCreate(
            name="Test Tool",
            slug="test-tool",
            description="Test tool desc",
            website_url="https://test.com",
            tags=["test", "ai"],
            features=["feature1"],
            quality_score=8,
            source="test"
        )
        
        result = self.service.insert_tool(tool_data)
        
        assert isinstance(result, Tool)
        assert result.name == "Test Tool"
        assert "ai" in result.tags

    @patch.object(db_connection, 'get_client')
    def test_bulk_insert_tools_success(self, mock_get_client):
        """Test successful bulk tool insertion"""
        mock_get_client.return_value = self.mock_client
        
        # Mock successful upsert responses
        mock_response = Mock()
        mock_response.data = [{'id': 1, 'name': 'Tool 1'}]
        self.mock_client.table.return_value.upsert.return_value.execute.return_value = mock_response
        
        tools = [
            ToolCreate(
                name="Tool 1", slug="tool-1", description="Desc 1",
                tags=["ai", "productivity"], quality_score=7, source="test"
            ),
            ToolCreate(
                name="Tool 2", slug="tool-2", description="Desc 2", 
                tags=["ai", "writing"], quality_score=8, source="test"
            )
        ]
        
        result = self.service.bulk_insert_tools(tools)
        
        assert result == 2
        assert self.mock_client.table.return_value.upsert.call_count == 2

    @patch.object(db_connection, 'get_client')
    def test_get_tools_by_tags(self, mock_get_client):
        """Test getting tools by tags"""
        mock_get_client.return_value = self.mock_client
        
        mock_response = Mock()
        mock_response.data = [{
            'id': 1, 'name': 'Tool 1', 'slug': 'tool-1',
            'description': 'Desc 1', 'website_url': 'https://test.com',
            'logo_url': None, 'pricing_type': 'free', 'price_range': None,
            'has_free_trial': False, 'tags': ['ai', 'writing'],
            'features': ['feature1'], 'quality_score': 8, 'popularity_score': 5,
            'is_featured': False, 'click_count': 0, 'source': 'test',
            'created_at': '2023-01-01T00:00:00Z', 'updated_at': '2023-01-01T00:00:00Z'
        }]
        
        # Setup chain of mock calls
        mock_table = Mock()
        mock_select = Mock()
        mock_overlaps = Mock()
        mock_order1 = Mock()
        mock_order2 = Mock()
        mock_limit = Mock()
        mock_offset = Mock()
        
        self.mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.overlaps.return_value = mock_overlaps
        mock_overlaps.order.return_value = mock_order1
        mock_order1.order.return_value = mock_order2
        mock_order2.limit.return_value = mock_limit
        mock_limit.offset.return_value = mock_offset
        mock_offset.execute.return_value = mock_response
        
        result = self.service.get_tools_by_tags(["ai"], limit=10, offset=0)
        
        assert len(result) == 1
        assert isinstance(result[0], Tool)
        assert result[0].name == "Tool 1"
        assert "ai" in result[0].tags

    @patch.object(db_connection, 'get_client')
    def test_get_all_tags(self, mock_get_client):
        """Test getting all unique tags"""
        mock_get_client.return_value = self.mock_client
        
        mock_response = Mock()
        mock_response.data = [
            {'tags': ['ai', 'writing']},
            {'tags': ['ai', 'productivity']},
            {'tags': ['design', 'ui']}
        ]
        
        mock_table = Mock()
        mock_select = Mock()
        
        self.mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.execute.return_value = mock_response
        
        result = self.service.get_all_tags()
        
        expected_tags = ['ai', 'design', 'productivity', 'ui', 'writing']
        assert result == expected_tags

    @patch.object(db_connection, 'get_client')
    def test_search_tools(self, mock_get_client):
        """Test searching tools by name and description"""
        mock_get_client.return_value = self.mock_client
        
        mock_response = Mock()
        mock_response.data = [{
            'id': 1, 'name': 'AI Writing Tool', 'slug': 'ai-writing-tool',
            'description': 'Tool for writing with AI', 'website_url': 'https://test.com',
            'logo_url': None, 'pricing_type': 'free', 'price_range': None,
            'has_free_trial': False, 'tags': ['ai', 'writing'],
            'features': ['nlp'], 'quality_score': 8, 'popularity_score': 5,
            'is_featured': False, 'click_count': 0, 'source': 'test',
            'created_at': '2023-01-01T00:00:00Z', 'updated_at': '2023-01-01T00:00:00Z'
        }]
        
        # Setup chain of mock calls
        mock_table = Mock()
        mock_select = Mock()
        mock_or = Mock()
        mock_order1 = Mock()
        mock_order2 = Mock()
        mock_limit = Mock()
        mock_offset = Mock()
        
        self.mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.or_.return_value = mock_or
        mock_or.order.return_value = mock_order1
        mock_order1.order.return_value = mock_order2
        mock_order2.limit.return_value = mock_limit
        mock_limit.offset.return_value = mock_offset
        mock_offset.execute.return_value = mock_response
        
        result = self.service.search_tools("writing", limit=10, offset=0)
        
        assert len(result) == 1
        assert isinstance(result[0], Tool)
        assert result[0].name == "AI Writing Tool"

    @patch.object(db_connection, 'get_client')
    def test_check_duplicate_tool_by_name(self, mock_get_client):
        """Test duplicate check by name"""
        mock_get_client.return_value = self.mock_client
        
        mock_response = Mock()
        mock_response.data = [{'id': 1}]  # Found duplicate
        
        mock_table = Mock()
        mock_select = Mock() 
        mock_ilike = Mock()
        
        self.mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.ilike.return_value = mock_ilike
        mock_ilike.execute.return_value = mock_response
        
        result = self.service.check_duplicate_tool(name="Test Tool")
        
        assert result is True
        mock_select.ilike.assert_called_with("name", "Test Tool")

    def test_generate_slug(self):
        """Test slug generation"""
        result = self.service.generate_slug("Test Tool Name!")
        assert result == "test-tool-name"
        
        result = self.service.generate_slug("AI & Machine Learning")
        assert result == "ai-machine-learning"


class TestDatabaseIntegration:
    """Integration tests for database functionality"""
    
    def test_db_connection_singleton(self):
        """Test that db_connection is a singleton"""
        from app.database.connection import db_connection as conn1
        from app.database.connection import db_connection as conn2
        assert conn1 is conn2

    def test_db_service_singleton(self):
        """Test that db_service is a singleton"""
        from app.database.service import db_service as service1
        from app.database.service import db_service as service2
        assert service1 is service2

    @patch.object(db_connection, 'get_client')
    def test_service_uses_connection(self, mock_get_client):
        """Test that service uses the connection properly"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # Mock empty response to avoid processing
        mock_response = Mock()
        mock_response.data = []
        mock_client.table.return_value.select.return_value.order.return_value.order.return_value.limit.return_value.offset.return_value.execute.return_value = mock_response
        
        db_service.get_all_tools()
        
        mock_get_client.assert_called_once()
        mock_client.table.assert_called_with("tools")


class TestDatabaseServiceEdgeCases:
    """Test edge cases and error handling"""
    
    def test_check_duplicate_tool_no_params(self):
        """Test duplicate check with no parameters"""
        result = db_service.check_duplicate_tool()
        assert result is False

    def test_generate_slug_long_text(self):
        """Test slug generation with very long text"""
        long_text = "A" * 300
        result = db_service.generate_slug(long_text)
        assert len(result) <= 200  # Should be truncated
        assert result == "a" * 200

    def test_generate_slug_empty_text(self):
        """Test slug generation with empty text"""
        result = db_service.generate_slug("")
        assert result == ""

    def test_generate_slug_special_characters(self):
        """Test slug generation with special characters"""
        result = db_service.generate_slug("Test@#$%^&*()Tool!")
        assert result == "test-tool"