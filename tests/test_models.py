import pytest
from pydantic import ValidationError
from app.models import Tool, ToolCreate



class TestToolModels:
    
    def test_tool_create_valid(self):
        """Test ToolCreate with valid data"""
        data = {
            "name": "Test Tool",
            "slug": "test-tool",
            "description": "A test tool",
            "website_url": "https://example.com",
            "pricing_type": "freemium",
            "has_free_trial": True,
            "tags": ["ai", "test"],
            "features": ["API"],
            "quality_score": 8
        }
        tool = ToolCreate(**data)
        assert tool.name == "Test Tool"
        assert tool.pricing_type == "freemium"
        assert tool.quality_score == 8

    def test_tool_create_minimal(self):
        """Test ToolCreate with minimal required data"""
        data = {
            "name": "Minimal Tool",
            "slug": "minimal-tool"
        }
        tool = ToolCreate(**data)
        assert tool.name == "Minimal Tool"
        assert tool.quality_score == 5  # Default
        assert tool.tags == []
        assert tool.features == []
        assert tool.popularity_score == 0

    def test_tool_create_invalid_pricing_type(self):
        """Test ToolCreate with invalid pricing type"""
        data = {
            "name": "Test Tool",
            "slug": "test-tool",
            "pricing_type": "invalid_type"
        }
        with pytest.raises(ValidationError):
            ToolCreate(**data)

    def test_tool_create_quality_score_bounds(self):
        """Test ToolCreate quality score validation"""
        # Valid scores
        for score in [1, 5, 10]:
            data = {
                "name": "Test Tool",
                "slug": "test-tool",
                "quality_score": score
            }
            tool = ToolCreate(**data)
            assert tool.quality_score == score

        # Invalid scores
        for score in [0, 11, -1]:
            data = {
                "name": "Test Tool",
                "slug": "test-tool",
                "quality_score": score
            }
            with pytest.raises(ValidationError):
                ToolCreate(**data)

    def test_tool_create_url_validation(self):
        """Test ToolCreate URL field length validation"""
        long_url = "https://" + "x" * 500  # Exceeds 500 char limit
        data = {
            "name": "Test Tool",
            "slug": "test-tool",
            "website_url": long_url
        }
        with pytest.raises(ValidationError):
            ToolCreate(**data)

    def test_tool_with_arrays(self):
        """Test Tool with tag and feature arrays"""
        data = {
            "name": "Feature Rich Tool",
            "slug": "feature-rich-tool",
            "tags": ["ai", "ml", "nlp", "automation"],
            "features": ["API", "Real-time", "Cloud", "Mobile"]
        }
        tool = ToolCreate(**data)
        assert len(tool.tags) == 4
        assert len(tool.features) == 4
        assert "ai" in tool.tags
        assert "API" in tool.features