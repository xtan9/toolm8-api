"""Basic tests to ensure core functionality works"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models import CategoryCreate, ToolCreate
from app.database.service import DatabaseService


class TestBasicFunctionality:
    
    def test_fastapi_app_creation(self):
        """Test FastAPI app can be created"""
        assert app is not None
        assert app.title == "ToolM8 Data Management API"

    def test_models_can_be_instantiated(self):
        """Test Pydantic models work correctly"""
        # Test CategoryCreate
        category = CategoryCreate(
            name="Test Category",
            slug="test-category",
            description="A test category"
        )
        assert category.name == "Test Category"
        assert category.slug == "test-category"
        
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

    def test_category_required_fields(self):
        """Test category model required fields"""
        # Should work with just name and slug
        category = CategoryCreate(name="Test", slug="test")
        assert category.name == "Test"
        assert category.slug == "test"
        assert category.display_order == 0  # Default
        assert category.is_featured is False  # Default

        # Should fail without required fields
        with pytest.raises(Exception):  # Pydantic ValidationError
            CategoryCreate(description="Missing required fields")