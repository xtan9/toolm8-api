import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from bs4 import BeautifulSoup
from app.scraper.theresanaiforthat import TheresAnAIForThatScraper
from app.models import ToolCreate


class TestTheresAnAIForThatScraper:
    
    @pytest.mark.asyncio
    async def test_scraper_initialization(self):
        """Test scraper initialization"""
        scraper = TheresAnAIForThatScraper()
        assert scraper.base_url == "https://theresanaiforthat.com"
        assert scraper.rate_limit_delay == 2.5
        assert isinstance(scraper.category_mapping, dict)

    @pytest.mark.asyncio 
    async def test_fetch_page_success(self, mock_aiohttp_session):
        """Test successful page fetching"""
        scraper = TheresAnAIForThatScraper()
        scraper.session = mock_aiohttp_session
        
        with patch('asyncio.sleep'):  # Skip rate limiting in tests
            result = await scraper.fetch_page("https://example.com")
        
        assert result == "<html><h1>Test Tool</h1></html>"

    @pytest.mark.asyncio
    async def test_fetch_page_failure(self):
        """Test page fetch failure"""
        scraper = TheresAnAIForThatScraper()
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_session.get.return_value.__aenter__.return_value = mock_response
        scraper.session = mock_session
        
        with patch('asyncio.sleep'):
            result = await scraper.fetch_page("https://example.com/404")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_page_exception(self):
        """Test page fetch with exception"""
        scraper = TheresAnAIForThatScraper()
        mock_session = AsyncMock()
        mock_session.get.side_effect = Exception("Network error")
        scraper.session = mock_session
        
        with patch('asyncio.sleep'):
            result = await scraper.fetch_page("https://example.com")
        
        assert result is None

    def test_extract_pricing_info_free(self):
        """Test pricing extraction for free tools"""
        scraper = TheresAnAIForThatScraper()
        
        result = scraper.extract_pricing_info("This is a free tool")
        assert result["pricing_type"] == "free"
        assert result["has_free_trial"] is False

    def test_extract_pricing_info_freemium(self):
        """Test pricing extraction for freemium tools"""
        scraper = TheresAnAIForThatScraper()
        
        result = scraper.extract_pricing_info("Free trial available, then paid")
        assert result["pricing_type"] == "freemium"
        assert result["has_free_trial"] is True

    def test_extract_pricing_info_paid(self):
        """Test pricing extraction for paid tools"""
        scraper = TheresAnAIForThatScraper()
        
        result = scraper.extract_pricing_info("$29/month subscription")
        assert result["pricing_type"] == "paid"
        assert result["has_free_trial"] is False

    def test_extract_pricing_info_one_time(self):
        """Test pricing extraction for one-time payment"""
        scraper = TheresAnAIForThatScraper()
        
        result = scraper.extract_pricing_info("One-time purchase for $99")
        assert result["pricing_type"] == "one-time"
        assert result["has_free_trial"] is False

    @pytest.mark.asyncio
    async def test_determine_category_id(self):
        """Test category determination"""
        scraper = TheresAnAIForThatScraper()
        
        # Mock the database service
        with patch('app.scraper.theresanaiforthat.db_service') as mock_db:
            mock_categories = [
                MagicMock(name="Writing & Content", id=1),
                MagicMock(name="Image Generation", id=2),
                MagicMock(name="Productivity", id=3)
            ]
            mock_db.get_all_categories.return_value = mock_categories
            
            # Test writing category detection
            category_id = await scraper.determine_category_id(
                ["writing", "content"], 
                "AI tool for writing and content creation"
            )
            assert category_id == 1
            
            # Test image category detection
            category_id = await scraper.determine_category_id(
                ["image", "generation"],
                "Generate images with AI"
            )
            assert category_id == 2
            
            # Test fallback to productivity
            category_id = await scraper.determine_category_id(
                ["unknown"],
                "Some unknown tool"
            )
            assert category_id == 3

    def test_clean_text(self):
        """Test text cleaning"""
        scraper = TheresAnAIForThatScraper()
        
        # Test normal text
        assert scraper.clean_text("  Normal text  ") == "Normal text"
        
        # Test text with special characters
        assert scraper.clean_text("Text@with#special$chars") == "Textwithspecialchars"
        
        # Test empty text
        assert scraper.clean_text("") == ""
        assert scraper.clean_text(None) == ""
        
        # Test very long text (should be truncated)
        long_text = "x" * 600
        result = scraper.clean_text(long_text)
        assert len(result) == 500

    def test_extract_features(self):
        """Test feature extraction"""
        scraper = TheresAnAIForThatScraper()
        
        description = "This tool has API access, real-time processing, and cloud storage"
        tags = ["automation", "ai-powered"]
        
        features = scraper.extract_features(description, tags)
        
        assert "API" in features
        assert "Real Time" in features
        assert "Cloud" in features
        assert "Automation" in features
        assert "Ai Powered" in features
        assert len(features) <= 10

    @pytest.mark.asyncio
    async def test_scrape_tool_page_success(self):
        """Test successful tool page scraping"""
        scraper = TheresAnAIForThatScraper()
        
        html_content = """
        <html>
            <head>
                <title>Amazing AI Tool</title>
                <meta name="description" content="An amazing AI tool for productivity">
            </head>
            <body>
                <h1>Amazing AI Tool</h1>
                <p>This is an amazing AI tool</p>
                <a class="website-link" href="https://amazing-tool.com">Visit</a>
                <span class="tag">productivity</span>
                <span class="tag">ai</span>
                <div class="pricing">Free trial available</div>
            </body>
        </html>
        """
        
        with patch.object(scraper, 'fetch_page', return_value=html_content):
            result = await scraper.scrape_tool_page("https://example.com/tool")
        
        assert result is not None
        assert result["name"] == "Amazing AI Tool"
        assert result["description"] == "An amazing AI tool for productivity"
        assert result["website_url"] == "https://amazing-tool.com"
        assert "productivity" in result["tags"]
        assert "ai" in result["tags"]
        assert result["pricing_type"] == "freemium"
        assert result["source"] == "theresanaiforthat"

    @pytest.mark.asyncio
    async def test_scrape_tool_page_no_title(self):
        """Test tool page scraping with no title"""
        scraper = TheresAnAIForThatScraper()
        
        html_content = "<html><body><p>No title</p></body></html>"
        
        with patch.object(scraper, 'fetch_page', return_value=html_content):
            result = await scraper.scrape_tool_page("https://example.com/tool")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_scrape_tool_page_fetch_failure(self):
        """Test tool page scraping when fetch fails"""
        scraper = TheresAnAIForThatScraper()
        
        with patch.object(scraper, 'fetch_page', return_value=None):
            result = await scraper.scrape_tool_page("https://example.com/tool")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_scrape_tools_listing(self):
        """Test scraping tools from listing page"""
        scraper = TheresAnAIForThatScraper()
        
        html_content = """
        <html>
            <body>
                <a href="/ai/tool1">Tool 1</a>
                <a href="/ai/tool2">Tool 2</a>
                <a href="/tool/tool3">Tool 3</a>
                <div class="tool-card">
                    <a href="/ai/tool4">Tool 4</a>
                </div>
                <a href="https://external.com">External Link</a>
            </body>
        </html>
        """
        
        with patch.object(scraper, 'fetch_page', return_value=html_content):
            result = await scraper.scrape_tools_listing("https://example.com/tools")
        
        assert len(result) == 4
        assert "https://theresanaiforthat.com/ai/tool1" in result
        assert "https://theresanaiforthat.com/ai/tool2" in result
        assert "https://theresanaiforthat.com/tool/tool3" in result
        assert "https://theresanaiforthat.com/ai/tool4" in result

    @pytest.mark.asyncio
    async def test_scrape_tools_listing_empty(self):
        """Test scraping empty tools listing"""
        scraper = TheresAnAIForThatScraper()
        
        with patch.object(scraper, 'fetch_page', return_value=None):
            result = await scraper.scrape_tools_listing("https://example.com/tools")
        
        assert result == []

    @pytest.mark.asyncio
    async def test_scrape_all_tools_integration(self):
        """Test full scraping process"""
        scraper = TheresAnAIForThatScraper()
        
        # Mock listing page
        listing_html = """
        <html><body>
            <a href="/ai/tool1">Tool 1</a>
            <a href="/ai/tool2">Tool 2</a>
        </body></html>
        """
        
        # Mock tool pages
        tool_html = """
        <html>
            <head><title>Test Tool</title></head>
            <body>
                <h1>Test Tool</h1>
                <p>Test description</p>
                <a class="visit" href="https://test-tool.com">Visit</a>
            </body>
        </html>
        """
        
        with patch.object(scraper, 'fetch_page') as mock_fetch:
            mock_fetch.side_effect = [listing_html, None, tool_html, tool_html]  # Empty second page
            
            with patch('app.scraper.theresanaiforthat.db_service') as mock_db:
                mock_db.generate_slug.side_effect = lambda x: x.lower().replace(" ", "-")
                mock_db.check_duplicate_tool.return_value = False
                mock_categories = [MagicMock(name="Productivity", id=1)]
                mock_db.get_all_categories.return_value = mock_categories
                
                result = await scraper.scrape_all_tools(max_pages=2)
        
        assert len(result) >= 1  # At least one valid tool
        assert all(isinstance(tool, ToolCreate) for tool in result)

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test scraper as async context manager"""
        async with TheresAnAIForThatScraper() as scraper:
            assert scraper.session is not None
        
        # Session should be closed after exiting context