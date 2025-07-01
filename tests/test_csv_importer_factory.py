"""Unit tests for CSV importer factory."""

import pytest
from app.services.csv_importer_factory import CSVImporterFactory
from app.services.base_csv_importer import BaseCSVImporter
from app.services.taaft_csv_importer import TAaftCSVImporter


class MockCSVImporter(BaseCSVImporter):
    """Mock CSV importer for testing."""
    
    @property
    def source_name(self):
        return "mock.com"
    
    def get_parser(self):
        return None


class TestCSVImporterFactory:
    """Test suite for CSV importer factory."""

    def setup_method(self):
        """Set up test fixtures."""
        # Store original importers to restore later
        self.original_importers = CSVImporterFactory._importers.copy()

    def teardown_method(self):
        """Clean up after tests."""
        # Restore original importers
        CSVImporterFactory._importers = self.original_importers

    def test_get_importer_taaft_source(self):
        """Test getting TAAFT importer with different source names."""
        # Test primary name
        importer = CSVImporterFactory.get_importer("taaft")
        assert isinstance(importer, TAaftCSVImporter)
        assert importer.source_name == "theresanaiforthat.com"
        
        # Test alias
        importer2 = CSVImporterFactory.get_importer("theresanaiforthat")
        assert isinstance(importer2, TAaftCSVImporter)
        
        # Test full domain alias
        importer3 = CSVImporterFactory.get_importer("theresanaiforthat.com")
        assert isinstance(importer3, TAaftCSVImporter)

    def test_get_importer_case_insensitive(self):
        """Test that source matching is case insensitive."""
        importer1 = CSVImporterFactory.get_importer("TAAFT")
        assert isinstance(importer1, TAaftCSVImporter)
        
        importer2 = CSVImporterFactory.get_importer("TheResAnAiForThat")
        assert isinstance(importer2, TAaftCSVImporter)

    def test_get_importer_with_whitespace(self):
        """Test that source matching handles whitespace."""
        importer = CSVImporterFactory.get_importer("  taaft  ")
        assert isinstance(importer, TAaftCSVImporter)

    def test_get_importer_unsupported_source(self):
        """Test getting importer for unsupported source."""
        with pytest.raises(ValueError, match="Unsupported source 'unknown'"):
            CSVImporterFactory.get_importer("unknown")

    def test_get_importer_empty_source(self):
        """Test getting importer with empty source."""
        with pytest.raises(ValueError, match="Unsupported source ''"):
            CSVImporterFactory.get_importer("")

    def test_register_importer_valid(self):
        """Test registering a new valid importer."""
        CSVImporterFactory.register_importer("mock", MockCSVImporter)
        
        # Verify it was registered
        assert "mock" in CSVImporterFactory._importers
        
        # Verify we can get it
        importer = CSVImporterFactory.get_importer("mock")
        assert isinstance(importer, MockCSVImporter)

    def test_register_importer_invalid_class(self):
        """Test registering an invalid importer class."""
        class InvalidImporter:
            pass
        
        with pytest.raises(ValueError, match="must inherit from BaseCSVImporter"):
            CSVImporterFactory.register_importer("invalid", InvalidImporter)

    def test_register_importer_overwrites_existing(self):
        """Test that registering overwrites existing importer."""
        # Register mock importer
        CSVImporterFactory.register_importer("taaft", MockCSVImporter)
        
        # Verify it was overwritten
        importer = CSVImporterFactory.get_importer("taaft")
        assert isinstance(importer, MockCSVImporter)
        assert importer.source_name == "mock.com"

    def test_get_supported_sources(self):
        """Test getting list of supported sources."""
        sources = CSVImporterFactory.get_supported_sources()
        
        assert isinstance(sources, list)
        assert "taaft" in sources
        assert "theresanaiforthat" in sources
        assert "theresanaiforthat.com" in sources

    def test_get_supported_sources_after_registration(self):
        """Test supported sources list updates after registration."""
        original_sources = CSVImporterFactory.get_supported_sources()
        
        CSVImporterFactory.register_importer("new_source", MockCSVImporter)
        
        updated_sources = CSVImporterFactory.get_supported_sources()
        assert len(updated_sources) == len(original_sources) + 1
        assert "new_source" in updated_sources

    def test_is_source_supported_true(self):
        """Test source support checking for supported sources."""
        assert CSVImporterFactory.is_source_supported("taaft") is True
        assert CSVImporterFactory.is_source_supported("TAAFT") is True
        assert CSVImporterFactory.is_source_supported("  theresanaiforthat  ") is True

    def test_is_source_supported_false(self):
        """Test source support checking for unsupported sources."""
        assert CSVImporterFactory.is_source_supported("unknown") is False
        assert CSVImporterFactory.is_source_supported("") is False
        assert CSVImporterFactory.is_source_supported("producthunt") is False

    def test_is_source_supported_after_registration(self):
        """Test source support checking after new registration."""
        assert CSVImporterFactory.is_source_supported("new_test") is False
        
        CSVImporterFactory.register_importer("new_test", MockCSVImporter)
        
        assert CSVImporterFactory.is_source_supported("new_test") is True

    def test_factory_singleton_behavior(self):
        """Test that factory maintains state across calls."""
        # Register a new importer
        CSVImporterFactory.register_importer("persistent", MockCSVImporter)
        
        # Verify it persists across different method calls
        assert CSVImporterFactory.is_source_supported("persistent") is True
        
        sources = CSVImporterFactory.get_supported_sources()
        assert "persistent" in sources
        
        importer = CSVImporterFactory.get_importer("persistent")
        assert isinstance(importer, MockCSVImporter)

    def test_multiple_registrations_same_source(self):
        """Test multiple registrations for the same source."""
        class AnotherMockImporter(BaseCSVImporter):
            @property
            def source_name(self):
                return "another.com"
            
            def get_parser(self):
                return None
        
        # Register first importer
        CSVImporterFactory.register_importer("test_source", MockCSVImporter)
        importer1 = CSVImporterFactory.get_importer("test_source")
        assert importer1.source_name == "mock.com"
        
        # Register second importer for same source
        CSVImporterFactory.register_importer("test_source", AnotherMockImporter)
        importer2 = CSVImporterFactory.get_importer("test_source")
        assert importer2.source_name == "another.com"

    def test_error_messages_include_available_sources(self):
        """Test that error messages include available sources."""
        try:
            CSVImporterFactory.get_importer("invalid_source")
        except ValueError as e:
            error_msg = str(e)
            assert "Available sources:" in error_msg
            assert "taaft" in error_msg
            assert "theresanaiforthat" in error_msg

    def test_importer_instances_are_fresh(self):
        """Test that each call to get_importer returns a new instance."""
        importer1 = CSVImporterFactory.get_importer("taaft")
        importer2 = CSVImporterFactory.get_importer("taaft")
        
        # Should be same type but different instances
        assert type(importer1) is type(importer2)
        assert importer1 is not importer2