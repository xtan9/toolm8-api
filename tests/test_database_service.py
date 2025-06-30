import pytest
from unittest.mock import AsyncMock, patch
from app.database.service import DatabaseService
from app.models import ToolCreate, Tool


class TestDatabaseService:
    
    def test_database_service_instantiation(self):
        """Test DatabaseService can be instantiated"""
        db_service = DatabaseService()
        assert db_service is not None

    def test_generate_slug(self):
        """Test slug generation"""
        db_service = DatabaseService()
        
        assert db_service.generate_slug("Test Tool Name") == "test-tool-name"
        assert db_service.generate_slug("AI & Machine Learning") == "ai-machine-learning"
        assert db_service.generate_slug("Special@Characters#Here!") == "specialcharactershere"

    def test_tag_based_functionality(self):
        """Test tag-based functionality exists"""
        db_service = DatabaseService()
        assert hasattr(db_service, 'get_tools_by_tags')
        assert hasattr(db_service, 'get_all_tags')
        assert hasattr(db_service, 'search_tools')