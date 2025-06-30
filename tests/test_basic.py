"""Basic tests to ensure core functionality works"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models import ToolCreate
from app.database.service import DatabaseService


class TestBasicFunctionality:
    
    def test_fastapi_app_creation(self):
        """Test FastAPI app can be created"""
        assert app is not None
        assert app.title == "ToolM8 Data Management API"

    def test_models_can_be_instantiated(self):
        """Test Pydantic models work correctly"""
        # Test ToolCreate
        tool = ToolCreate(
            name="Test Tool",
            slug="test-tool",
            description="A test tool",
            pricing_type="free"
        )
        assert tool.name == "Test Tool"
        assert tool.pricing_type == "free"
        assert tool.quality_score == 5  # Default value
        assert tool.tags == []  # Default empty list
        assert tool.features == []  # Default empty list

    def test_database_service_creation(self):
        """Test DatabaseService can be instantiated"""
        db_service = DatabaseService()
        assert db_service is not None

    def test_slug_generation(self):
        """Test slug generation functionality"""
        db_service = DatabaseService()
        assert db_service.generate_slug("Test Tool Name") == "test-tool-name"
        assert db_service.generate_slug("AI & Machine Learning") == "ai-machine-learning"


class TestAPIBasics:
    
    def test_root_endpoint(self):
        """Test API root endpoint"""
        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "ToolM8 Data Management API" in data["message"]

    def test_health_endpoint(self):
        """Test health check endpoint"""
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "toolm8-data-api"

    def test_404_endpoint(self):
        """Test non-existent endpoint returns 404"""
        client = TestClient(app)
        response = client.get("/non-existent")
        assert response.status_code == 404

    def test_invalid_method(self):
        """Test invalid HTTP method returns 405"""
        client = TestClient(app)
        response = client.put("/admin/stats")  # Use existing endpoint
        assert response.status_code == 405


class TestModelValidation:
    
    def test_tool_pricing_type_validation(self):
        """Test tool pricing type validation"""
        # Valid pricing types
        for pricing_type in ["free", "freemium", "paid", "one-time"]:
            tool = ToolCreate(
                name="Test Tool",
                slug="test-tool",
                pricing_type=pricing_type
            )
            assert tool.pricing_type == pricing_type

        # Invalid pricing type should raise ValidationError
        with pytest.raises(Exception):  # Pydantic ValidationError
            ToolCreate(
                name="Test Tool",
                slug="test-tool",
                pricing_type="invalid_type"
            )

    def test_tool_quality_score_bounds(self):
        """Test tool quality score validation"""
        # Valid scores (1-10)
        for score in [1, 5, 10]:
            tool = ToolCreate(
                name="Test Tool",
                slug="test-tool",
                quality_score=score
            )
            assert tool.quality_score == score

        # Invalid scores should raise ValidationError
        for score in [0, 11, -1]:
            with pytest.raises(Exception):  # Pydantic ValidationError
                ToolCreate(
                    name="Test Tool",
                    slug="test-tool",
                    quality_score=score
                )

    def test_tool_tags_and_features(self):
        """Test tool tags and features validation"""
        tool = ToolCreate(
            name="Test Tool",
            slug="test-tool",
            tags=["ai", "productivity"],
            features=["real-time", "api"]
        )
        assert tool.tags == ["ai", "productivity"]
        assert tool.features == ["real-time", "api"]
        
        # Empty lists should work
        tool_empty = ToolCreate(
            name="Empty Tool",
            slug="empty-tool"
        )
        assert tool_empty.tags == []
        assert tool_empty.features == []