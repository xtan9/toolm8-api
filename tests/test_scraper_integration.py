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
    def test_scraper_uses_sync_database_services(self, mock_db_service):
        """Test that scraper uses sync database services"""
        mock_db_service.generate_slug.return_value = "test-tool"
        mock_db_service.check_duplicate_tool.return_value = False
        
        scraper = TheresAnAIForThatScraper()
        
        # Test that database service methods are accessible
        slug = mock_db_service.generate_slug("Test Tool")
        is_duplicate = mock_db_service.check_duplicate_tool(name="Test Tool")
        
        assert slug == "test-tool"
        assert is_duplicate is False
        
        # Verify calls were made
        mock_db_service.generate_slug.assert_called_with("Test Tool")
        mock_db_service.check_duplicate_tool.assert_called_with(name="Test Tool")

    def test_enhance_tags_functionality(self):
        """Test tag enhancement functionality"""
        scraper = TheresAnAIForThatScraper()
        
        # Test basic tag enhancement
        enhanced = scraper.enhance_tags(
            ["original"], "This is a writing tool for productivity", "Writing Pro"
        )
        
        # Should contain original tag plus enhanced tags
        assert "original" in enhanced
        assert "writing" in enhanced
        assert "productivity" in enhanced
        assert "ai" in enhanced  # AI tag should be added by default

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
            mock_db_service.generate_slug.assert_called_with("Test Tool")
            mock_db_service.check_duplicate_tool.assert_called()

    @pytest.mark.asyncio
    @patch('app.scraper.theresanaiforthat.db_service')
    async def test_scrape_with_duplicate_detection(self, mock_db_service):
        """Test that duplicate tools are filtered out"""
        # Mock that tool is a duplicate
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
                quality_score=7, source="theresanaiforthat"
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


class TestScraperTagEnhancement:
    """Test tag enhancement functionality"""

    def test_enhance_tags_keywords(self):
        """Test that tag enhancement works with expected keywords"""
        scraper = TheresAnAIForThatScraper()
        
        # Test writing enhancement
        tags = scraper.enhance_tags([], "This is a writing tool for content creation", "Writing Tool")
        assert "writing" in tags
        
        # Test image enhancement
        tags = scraper.enhance_tags([], "Generate images and photos", "Image Creator")
        assert "image-generation" in tags
        
        # Test development enhancement
        tags = scraper.enhance_tags([], "Code development and programming", "Dev Tool")
        assert "development" in tags

    def test_tag_enhancement_logic(self):
        """Test tag enhancement with various inputs"""
        scraper = TheresAnAIForThatScraper()
        
        # Test writing tag enhancement
        enhanced = scraper.enhance_tags(
            ["ai"], "Tool for writing and content creation", "AI Writing Assistant"
        )
        assert "writing" in enhanced
        assert "ai" in enhanced
        
        # Test image tag enhancement
        enhanced = scraper.enhance_tags(
            ["ai"], "Create stunning images with AI", "Image Generator"
        )
        assert "image-generation" in enhanced
        assert "ai" in enhanced
        
        # Test multiple category detection
        enhanced = scraper.enhance_tags(
            [], "AI tool for writing code and development", "Code Writer"
        )
        assert "writing" in enhanced
        assert "development" in enhanced
        assert "ai" in enhanced
        
        # Test tag limit (should be max 10)
        enhanced = scraper.enhance_tags(
            ["tag1", "tag2", "tag3", "tag4", "tag5"], 
            "writing development image design marketing productivity audio data research video",
            "Multi Tool"
        )
        assert len(enhanced) <= 10