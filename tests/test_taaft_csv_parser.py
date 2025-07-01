"""Unit tests for TAAFT CSV parser."""

import pytest
from unittest.mock import patch
import pandas as pd

from app.services.csv_parser import TAaftCSVParser


class TestTAaftCSVParser:
    """Test suite for TAAFT CSV parser."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = TAaftCSVParser()

    def test_source_name(self):
        """Test source name property."""
        assert self.parser.source_name == "theresanaiforthat.com"

    def test_expected_columns(self):
        """Test expected columns property."""
        expected = [
            "ai_link",
            "task_label",
            "external_ai_link href",
            "taaft_icon src",
            "ai_launch_date",
            "stats_views",
            "saves",
            "average_rating",
            "comment_body",
        ]
        assert self.parser.expected_columns == expected

    def test_validate_csv_format_valid(self):
        """Test CSV format validation with valid data."""
        csv_content = '''ai_link,task_label,external_ai_link href
ChatGPT,Writing,https://openai.com/chatgpt
Midjourney,Image Generation,https://midjourney.com'''
        
        assert self.parser.validate_csv_format(csv_content) is True

    def test_validate_csv_format_missing_required_column(self):
        """Test CSV format validation with missing required column."""
        csv_content = '''task_label,external_ai_link href
Writing,https://openai.com/chatgpt'''
        
        with pytest.raises(ValueError, match="Missing required TAAFT columns"):
            self.parser.validate_csv_format(csv_content)

    def test_validate_csv_format_invalid_csv(self):
        """Test CSV format validation with invalid CSV."""
        csv_content = "not,a,valid,csv\nfile"
        
        # This should fail validation since it doesn't have required columns
        with pytest.raises(ValueError, match="Invalid TAAFT CSV format"):
            self.parser.validate_csv_format(csv_content)

    def test_get_sample_csv_format(self):
        """Test sample CSV format string."""
        sample = self.parser.get_sample_csv_format()
        assert "TAAFT CSV format" in sample
        assert "ai_link" in sample
        assert "ChatGPT" in sample

    def test_parse_csv_content_valid_data(self):
        """Test parsing valid CSV content."""
        csv_content = '''taaft_icon src,ai_link,external_ai_link href,task_label,ai_launch_date,stats_views,saves,average_rating,comment_body
https://example.com/icon.svg,ChatGPT,https://openai.com/chatgpt,Writing,Free + from $20/mo,1500,25,4.5,Great AI tool
https://example.com/icon2.svg,Midjourney,https://midjourney.com,Image Generation,From $10/mo,2500,40,4.8,Amazing image generator'''
        
        tools = self.parser.parse_csv_content(csv_content)
        
        assert len(tools) == 2
        
        # Test first tool
        tool1 = tools[0]
        assert tool1["name"] == "ChatGPT"
        assert tool1["slug"] == "chatgpt"
        assert tool1["source"] == "theresanaiforthat.com"
        assert tool1["pricing_type"] == "freemium"
        assert tool1["quality_score"] >= 1
        assert tool1["popularity_score"] >= 0
        assert isinstance(tool1["tags"], list) or tool1["tags"] is None
        assert isinstance(tool1["features"], list) or tool1["features"] is None

    def test_parse_csv_content_empty_data(self):
        """Test parsing CSV with no valid tools."""
        csv_content = '''ai_link,task_label
,
,Writing'''
        
        tools = self.parser.parse_csv_content(csv_content)
        assert len(tools) == 0

    def test_clean_string_valid(self):
        """Test string cleaning with valid input."""
        assert self.parser.clean_string("  test  ") == "test"
        assert self.parser.clean_string("normal") == "normal"

    def test_clean_string_invalid(self):
        """Test string cleaning with invalid input."""
        assert self.parser.clean_string(None) is None
        assert self.parser.clean_string("") is None
        assert self.parser.clean_string("   ") is None
        assert self.parser.clean_string(pd.NA) is None

    def test_generate_slug(self):
        """Test slug generation."""
        assert self.parser.generate_slug("ChatGPT") == "chatgpt"
        assert self.parser.generate_slug("GPT-4 Turbo") == "gpt-4-turbo"
        assert self.parser.generate_slug("Test!@# Tool") == "test-tool"
        assert self.parser.generate_slug("  Multiple   Spaces  ") == "multiple-spaces"

    def test_clean_url_valid(self):
        """Test URL cleaning with valid URLs."""
        url = "https://example.com/tool?utm_source=test&ref=taaft"
        cleaned = self.parser.clean_url(url)
        assert "utm_source" not in cleaned
        assert "ref" not in cleaned
        assert "example.com/tool" in cleaned

    def test_clean_url_invalid(self):
        """Test URL cleaning with invalid input."""
        assert self.parser.clean_url(None) is None
        assert self.parser.clean_url("") == ""  # Empty string returns empty string
        assert self.parser.clean_url(pd.NA) is None

    def test_extract_pricing_type(self):
        """Test pricing type extraction."""
        assert self.parser.extract_pricing_type("100% free") == "free"
        assert self.parser.extract_pricing_type("Free + from $20/mo") == "freemium"
        assert self.parser.extract_pricing_type("From $10/mo") == "paid"
        assert self.parser.extract_pricing_type("One-time $50") == "one-time"
        assert self.parser.extract_pricing_type(None) == "no-pricing"
        assert self.parser.extract_pricing_type("") == "no-pricing"

    def test_extract_price_range(self):
        """Test price range extraction."""
        assert self.parser.extract_price_range("Free + from $20/mo") == "$20/month"
        assert self.parser.extract_price_range("From $10/mo") == "$10/month"
        assert self.parser.extract_price_range(None) is None

    def test_extract_has_free_trial(self):
        """Test free trial detection."""
        assert self.parser.extract_has_free_trial("Free trial available") is True
        assert self.parser.extract_has_free_trial("100% free") is True
        assert self.parser.extract_has_free_trial("Paid only") is False
        assert self.parser.extract_has_free_trial(None) is False

    def test_extract_tags(self):
        """Test tag extraction."""
        row = pd.Series({
            "task_label": "Writing",
            "ai_launch_date": "Free + from $20/mo"
        })
        
        tags = self.parser.extract_tags(row)
        assert "writing" in tags
        assert "freemium" in tags

    def test_extract_features(self):
        """Test feature extraction."""
        row = pd.Series({
            "average_rating": "4.5",
            "comment_body": "Great tool for writing"
        })
        
        features = self.parser.extract_features(row)
        if features:  # Features might be None
            assert isinstance(features, list)

    def test_calculate_quality_score_high_rating(self):
        """Test quality score calculation with high rating."""
        row = pd.Series({
            "average_rating": "4.8",
            "saves": "100",
            "comment_body": "Excellent tool"
        })
        
        score = self.parser.calculate_quality_score(row)
        assert 1 <= score <= 10
        assert score > 5  # Should be above base score due to high rating

    def test_calculate_quality_score_low_data(self):
        """Test quality score calculation with minimal data."""
        row = pd.Series({})
        
        score = self.parser.calculate_quality_score(row)
        assert 1 <= score <= 10
        assert score == 5  # Base score

    def test_calculate_popularity_score(self):
        """Test popularity score calculation."""
        row = pd.Series({
            "stats_views": "1,500",
            "saves": "25"
        })
        
        score = self.parser.calculate_popularity_score(row)
        assert score >= 0
        assert isinstance(score, int)

    def test_transform_row_complete_data(self):
        """Test row transformation with complete data."""
        row = pd.Series({
            "ai_link": "ChatGPT",
            "task_label": "Writing",
            "external_ai_link href": "https://openai.com/chatgpt",
            "taaft_icon src": "https://example.com/icon.svg",
            "ai_launch_date": "Free + from $20/mo",
            "stats_views": "1,500",
            "saves": "25",
            "average_rating": "4.5",
            "comment_body": "Great AI tool"
        })
        
        tool = self.parser.transform_row(row)
        
        assert tool is not None
        assert tool["name"] == "ChatGPT"
        assert tool["slug"] == "chatgpt"
        assert tool["source"] == "theresanaiforthat.com"
        assert "website_url" in tool
        assert "logo_url" in tool
        assert "pricing_type" in tool
        assert "quality_score" in tool
        assert "popularity_score" in tool

    def test_transform_row_missing_name(self):
        """Test row transformation with missing name."""
        row = pd.Series({
            "ai_link": "",
            "task_label": "Writing"
        })
        
        tool = self.parser.transform_row(row)
        assert tool is None

    @patch('app.services.csv_parser.logger')
    def test_parse_csv_content_with_invalid_row(self, mock_logger):
        """Test parsing CSV with some invalid rows."""
        csv_content = '''ai_link,task_label
Valid Tool,Writing
,Invalid Row
Another Tool,Image Generation'''
        
        tools = self.parser.parse_csv_content(csv_content)
        
        # Should get 2 valid tools, 1 invalid row skipped
        assert len(tools) == 2
        assert tools[0]["name"] == "Valid Tool"
        assert tools[1]["name"] == "Another Tool"

    def test_extract_description(self):
        """Test description extraction."""
        # Test with comment body
        row1 = pd.Series({
            "task_label": "Writing", 
            "comment_body": "This is a detailed description of the tool"
        })
        desc1 = self.parser.extract_description(row1)
        assert "Writing." in desc1
        assert "detailed description" in desc1
        
        # Test with only task label
        row2 = pd.Series({
            "task_label": "Image Generation",
            "comment_body": ""
        })
        desc2 = self.parser.extract_description(row2)
        assert "Image Generation" in desc2
        
        # Test with minimal data
        row3 = pd.Series({})
        desc3 = self.parser.extract_description(row3)
        assert "AI tool" in desc3