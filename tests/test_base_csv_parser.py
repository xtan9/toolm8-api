"""Unit tests for base CSV parser."""

import pytest
from app.services.base_csv_parser import BaseCSVParser


class MockCSVParser(BaseCSVParser):
    """Mock CSV parser for testing."""
    
    @property
    def source_name(self):
        return "mock.com"
    
    @property
    def expected_columns(self):
        return ["name", "description", "url"]
    
    def validate_csv_format(self, csv_content):
        if "invalid" in csv_content:
            raise ValueError("Invalid format")
        return True
    
    def parse_csv_content(self, csv_content):
        return [
            {
                "name": "Test Tool",
                "slug": "test-tool",
                "description": "A test tool",
                "website_url": "https://test.com",
                "logo_url": None,
                "pricing_type": "free",
                "price_range": None,
                "has_free_trial": False,
                "tags": ["test"],
                "features": None,
                "quality_score": 5,
                "popularity_score": 10,
                "is_featured": False,
                "source": "mock.com"
            }
        ]


class TestBaseCSVParser:
    """Test suite for base CSV parser."""

    def test_abstract_class_cannot_be_instantiated(self):
        """Test that BaseCSVParser cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseCSVParser()

    def test_mock_parser_implements_abstract_methods(self):
        """Test that mock parser properly implements all abstract methods."""
        parser = MockCSVParser()
        
        # Test properties
        assert parser.source_name == "mock.com"
        assert parser.expected_columns == ["name", "description", "url"]
        
        # Test methods
        assert parser.validate_csv_format("valid content") is True
        
        with pytest.raises(ValueError):
            parser.validate_csv_format("invalid content")
        
        tools = parser.parse_csv_content("test content")
        assert len(tools) == 1
        assert tools[0]["name"] == "Test Tool"

    def test_get_sample_csv_format_default(self):
        """Test default sample CSV format method."""
        parser = MockCSVParser()
        sample = parser.get_sample_csv_format()
        
        assert "Sample CSV format for mock.com" in sample
        assert "Override get_sample_csv_format()" in sample

    def test_standard_tool_format_validation(self):
        """Test that parsed tools conform to expected standard format."""
        parser = MockCSVParser()
        tools = parser.parse_csv_content("test")
        
        assert len(tools) == 1
        tool = tools[0]
        
        # Verify all required fields are present
        required_fields = [
            "name", "slug", "description", "website_url", "logo_url",
            "pricing_type", "price_range", "has_free_trial", "tags",
            "features", "quality_score", "popularity_score", "is_featured", "source"
        ]
        
        for field in required_fields:
            assert field in tool, f"Missing required field: {field}"
        
        # Verify field types
        assert isinstance(tool["name"], str)
        assert isinstance(tool["slug"], str)
        assert isinstance(tool["description"], str)
        assert isinstance(tool["quality_score"], int)
        assert isinstance(tool["popularity_score"], int)
        assert isinstance(tool["is_featured"], bool)
        assert isinstance(tool["has_free_trial"], bool)
        assert isinstance(tool["source"], str)
        
        # Verify field constraints
        assert 1 <= tool["quality_score"] <= 10
        assert tool["popularity_score"] >= 0
        assert tool["pricing_type"] in ["free", "paid", "freemium", "one-time", "no-pricing"]

    def test_expected_columns_property(self):
        """Test that expected_columns property returns list of strings."""
        parser = MockCSVParser()
        columns = parser.expected_columns
        
        assert isinstance(columns, list)
        assert all(isinstance(col, str) for col in columns)
        assert len(columns) > 0

    def test_source_name_property(self):
        """Test that source_name property returns string."""
        parser = MockCSVParser()
        source = parser.source_name
        
        assert isinstance(source, str)
        assert len(source) > 0


class IncompleteParser(BaseCSVParser):
    """Parser missing some abstract methods for testing."""
    
    @property
    def source_name(self):
        return "incomplete.com"


class TestAbstractMethodEnforcement:
    """Test that abstract methods are properly enforced."""

    def test_missing_expected_columns_property(self):
        """Test that missing expected_columns property prevents instantiation."""
        with pytest.raises(TypeError):
            IncompleteParser()

    def test_all_abstract_methods_required(self):
        """Test that all abstract methods must be implemented."""
        
        class PartialParser(BaseCSVParser):
            @property
            def source_name(self):
                return "partial.com"
            
            @property  
            def expected_columns(self):
                return ["name"]
            
            # Missing: validate_csv_format and parse_csv_content
        
        with pytest.raises(TypeError):
            PartialParser()

    def test_complete_implementation_works(self):
        """Test that complete implementation can be instantiated."""
        
        class CompleteParser(BaseCSVParser):
            @property
            def source_name(self):
                return "complete.com"
            
            @property
            def expected_columns(self):
                return ["name", "url"]
            
            def validate_csv_format(self, csv_content):
                return True
            
            def parse_csv_content(self, csv_content):
                return []
        
        # This should work without errors
        parser = CompleteParser()
        assert parser.source_name == "complete.com"
        assert parser.expected_columns == ["name", "url"]