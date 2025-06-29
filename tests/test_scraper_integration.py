import pytest
import pytest_asyncio
from unittest.mock import Mock, patch, AsyncMock
from app.scraper.theresanaiforthat import TheresAnAIForThatScraper, run_scraper
from app.models import ToolCreate


class TestScraperDatabaseIntegration:
    """Test scraper integration with database services"""

    @pytest.fixture
    def scraper(self):
        return TheresAnAIForThatScraper()

    @patch('app.scraper.theresanaiforthat.db_service')
    def test_determine_category_id_uses_sync_service(self, mock_db_service):
        """Test that determine_category_id uses sync database service"""
        from app.models import Category
        
        # Mock categories response
        mock_categories = [
            Category(
                id=1, name="Writing & Content", slug="writing-content",
                description="Writing tools", display_order=1, is_featured=True,
                created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"
            ),
            Category(
                id=2, name="Image Generation", slug="image-generation", 
                description="Image tools", display_order=2, is_featured=True,
                created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"
            )
        ]
        mock_db_service.get_all_categories.return_value = mock_categories
        
        scraper = TheresAnAIForThatScraper()
        
        # This should be an async function that calls sync db_service
        async def test_async():
            category_id = await scraper.determine_category_id(
                tags=["writing", "content"], 
                description="A tool for writing content"
            )
            return category_id
        
        import asyncio
        result = asyncio.run(test_async())
        
        # Should call sync method, not async
        mock_db_service.get_all_categories.assert_called_once()
        assert result == 1  # Should match "Writing & Content"

    @patch('app.scraper.theresanaiforthat.db_service')
    def test_determine_category_id_fallback(self, mock_db_service):
        """Test category determination fallback to Productivity"""
        from app.models import Category
        
        mock_categories = [
            Category(
                id=9, name="Productivity", slug="productivity",
                description="Productivity tools", display_order=9, is_featured=True,
                created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"
            )
        ]
        mock_db_service.get_all_categories.return_value = mock_categories
        
        scraper = TheresAnAIForThatScraper()
        
        async def test_async():
            # Use tags that don't match any category mapping
            category_id = await scraper.determine_category_id(
                tags=["unknown", "unmatched"],
                description="Some unknown tool"
            )
            return category_id
        
        import asyncio
        result = asyncio.run(test_async())
        
        assert result == 9  # Should fallback to Productivity

    @pytest.mark.asyncio
    async def test_scrape_tool_page_duplicate_check_sync(self):
        """Test that tool scraping uses sync duplicate check"""
        scraper = TheresAnAIForThatScraper()
        
        with patch.object(scraper, 'fetch_page') as mock_fetch, \
             patch('app.scraper.theresanaiforthat.db_service') as mock_db_service:
            
            # Mock HTML content
            mock_fetch.return_value = """
            <html>
                <head><title>Test Tool</title></head>
                <body>
                    <h1>Test Tool</h1>
                    <p>A great testing tool</p>
                    <a href="https://testtool.com" class="visit-website">Visit</a>
                </body>
            </html>
            """
            
            # Mock database responses
            mock_db_service.get_all_categories.return_value = []
            mock_db_service.generate_slug.return_value = "test-tool"
            mock_db_service.check_duplicate_tool.return_value = False
            
            result = await scraper.scrape_tool_page("https://example.com/tool")
            
            assert result is not None
            assert result["name"] == "Test Tool"
            # Don't check for slug since it's added later in the scraping process

    @pytest.mark.asyncio
    @patch('app.scraper.theresanaiforthat.db_service')
    async def test_scrape_all_tools_integration(self, mock_db_service):
        """Test complete scraping flow with database integration"""
        # Mock database services
        mock_db_service.get_all_categories.return_value = []
        mock_db_service.generate_slug.return_value = "test-tool"
        mock_db_service.check_duplicate_tool.return_value = False
        
        scraper = TheresAnAIForThatScraper()
        
        with patch.object(scraper, 'scrape_tools_listing') as mock_listing, \
             patch.object(scraper, 'scrape_tool_page') as mock_tool_page:
            
            # Mock tool listing
            mock_listing.return_value = ["https://example.com/tool1"]
            
            # Mock tool page scraping
            mock_tool_page.return_value = {
                "name": "Test Tool",
                "description": "A test tool",
                "website_url": "https://testtool.com",
                "tags": ["test"],
                "features": ["testing"],
                "quality_score": 8,
                "source": "theresanaiforthat"
            }
            
            tools = await scraper.scrape_all_tools(max_pages=1)
            
            assert len(tools) == 1
            assert isinstance(tools[0], ToolCreate)
            assert tools[0].name == "Test Tool"
            
            # Verify sync database methods were called
            mock_db_service.get_all_categories.assert_called()
            mock_db_service.generate_slug.assert_called_with("Test Tool")
            mock_db_service.check_duplicate_tool.assert_called()

    @pytest.mark.asyncio
    @patch('app.scraper.theresanaiforthat.db_service')
    async def test_scrape_with_duplicate_detection(self, mock_db_service):
        """Test that duplicate tools are filtered out"""
        # Mock that tool is a duplicate
        mock_db_service.get_all_categories.return_value = []
        mock_db_service.generate_slug.return_value = "duplicate-tool"
        mock_db_service.check_duplicate_tool.return_value = True  # Is duplicate
        
        scraper = TheresAnAIForThatScraper()
        
        with patch.object(scraper, 'scrape_tools_listing') as mock_listing, \
             patch.object(scraper, 'scrape_tool_page') as mock_tool_page:
            
            mock_listing.return_value = ["https://example.com/duplicate"]
            mock_tool_page.return_value = {
                "name": "Duplicate Tool",
                "description": "This tool already exists",
                "website_url": "https://duplicate.com",
                "tags": ["duplicate"],
                "features": ["existing"],
                "quality_score": 5,
                "source": "theresanaiforthat"
            }
            
            tools = await scraper.scrape_all_tools(max_pages=1)
            
            # Should return empty list due to duplicate
            assert len(tools) == 0
            
            # Should still check for duplicates
            mock_db_service.check_duplicate_tool.assert_called()


class TestRunScraperFunction:
    """Test the run_scraper async function"""

    @pytest.mark.asyncio
    @patch('app.scraper.theresanaiforthat.db_service')
    async def test_run_scraper_success(self, mock_db_service):
        """Test successful scraper run"""
        mock_db_service.bulk_insert_tools.return_value = 5
        
        # Create a mock scraper that returns tools
        mock_tools = [
            ToolCreate(
                name=f"Tool {i}", slug=f"tool-{i}", description=f"Description {i}",
                category_id=1, quality_score=7, source="theresanaiforthat"
            ) for i in range(5)
        ]
        
        with patch('app.scraper.theresanaiforthat.TheresAnAIForThatScraper') as MockScraper:
            mock_instance = AsyncMock()
            mock_instance.scrape_all_tools.return_value = mock_tools
            MockScraper.return_value.__aenter__.return_value = mock_instance
            
            await run_scraper()
            
            # Should call bulk insert with sync method
            mock_db_service.bulk_insert_tools.assert_called_once_with(mock_tools)

    @pytest.mark.asyncio
    @patch('app.scraper.theresanaiforthat.db_service')
    async def test_run_scraper_no_tools(self, mock_db_service):
        """Test scraper run when no tools are found"""
        with patch('app.scraper.theresanaiforthat.TheresAnAIForThatScraper') as MockScraper:
            mock_instance = AsyncMock()
            mock_instance.scrape_all_tools.return_value = []  # No tools
            MockScraper.return_value.__aenter__.return_value = mock_instance
            
            await run_scraper()
            
            # Should not call bulk insert
            mock_db_service.bulk_insert_tools.assert_not_called()

    @pytest.mark.asyncio
    @patch('app.scraper.theresanaiforthat.db_service')
    async def test_run_scraper_exception_handling(self, mock_db_service):
        """Test scraper handles exceptions gracefully"""
        with patch('app.scraper.theresanaiforthat.TheresAnAIForThatScraper') as MockScraper:
            mock_instance = AsyncMock()
            mock_instance.scrape_all_tools.side_effect = Exception("Scraping failed")
            MockScraper.return_value.__aenter__.return_value = mock_instance
            
            # Should not raise exception
            await run_scraper()
            
            # Should not call database operations
            mock_db_service.bulk_insert_tools.assert_not_called()

    @pytest.mark.asyncio
    @patch('app.scraper.theresanaiforthat.logger')
    @patch('app.scraper.theresanaiforthat.db_service')
    async def test_run_scraper_logging(self, mock_db_service, mock_logger):
        """Test that scraper logs appropriately"""
        mock_tools = [ToolCreate(
            name="Test Tool", slug="test-tool", description="Test",
            category_id=1, quality_score=8, source="theresanaiforthat"
        )]
        mock_db_service.bulk_insert_tools.return_value = 1
        
        with patch('app.scraper.theresanaiforthat.TheresAnAIForThatScraper') as MockScraper:
            mock_instance = AsyncMock()
            mock_instance.scrape_all_tools.return_value = mock_tools
            MockScraper.return_value.__aenter__.return_value = mock_instance
            
            await run_scraper()
            
            # Should log insertion info
            mock_logger.info.assert_any_call("Inserting 1 tools into database...")
            mock_logger.info.assert_any_call("Successfully inserted 1 tools")


class TestScraperCategoryMapping:
    """Test category mapping functionality"""

    def test_category_mapping_keywords(self):
        """Test that category mapping contains expected keywords"""
        scraper = TheresAnAIForThatScraper()
        
        # Verify some key mappings exist
        assert "writing" in scraper.category_mapping
        assert "image" in scraper.category_mapping
        assert "code" in scraper.category_mapping
        assert "data" in scraper.category_mapping
        
        # Verify mappings point to expected categories
        assert "Writing & Content" in scraper.category_mapping["writing"]
        assert "Image Generation" in scraper.category_mapping["image"]
        assert "Code & Development" in scraper.category_mapping["code"]
        assert "Data & Analytics" in scraper.category_mapping["data"]

    @pytest.mark.asyncio
    @patch('app.scraper.theresanaiforthat.db_service')
    async def test_category_determination_logic(self, mock_db_service):
        """Test category determination with various inputs"""
        from app.models import Category
        
        # Mock all categories
        mock_categories = [
            Category(id=1, name="Writing & Content", slug="writing-content",
                    description="", display_order=1, is_featured=True,
                    created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"),
            Category(id=2, name="Image Generation", slug="image-generation", 
                    description="", display_order=2, is_featured=True,
                    created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"),
            Category(id=3, name="Code & Development", slug="code-development",
                    description="", display_order=3, is_featured=True, 
                    created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"),
            Category(id=9, name="Productivity", slug="productivity",
                    description="", display_order=9, is_featured=True,
                    created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z")
        ]
        mock_db_service.get_all_categories.return_value = mock_categories
        
        scraper = TheresAnAIForThatScraper()
        
        # Test writing category
        result = await scraper.determine_category_id(
            tags=["writing", "content"], 
            description="A writing assistant"
        )
        assert result == 1
        
        # Test image category  
        result = await scraper.determine_category_id(
            tags=["image", "generator"],
            description="Generate images with AI"
        )
        assert result == 2
        
        # Test code category
        result = await scraper.determine_category_id(
            tags=["programming", "developer"],
            description="Code assistance tool"
        )
        assert result == 3
        
        # Test fallback to productivity
        result = await scraper.determine_category_id(
            tags=["unknown", "misc"],
            description="Some random tool"
        )
        assert result == 9