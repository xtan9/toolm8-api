"""CSV parser service for ProductHunt data - EXAMPLE implementation."""

import logging
import re
from io import StringIO
from typing import Any, Dict, List

import pandas as pd

from app.services.base_csv_parser import BaseCSVParser

logger = logging.getLogger(__name__)


class ProductHuntCSVParser(BaseCSVParser):
    """Example parser for ProductHunt CSV data format."""

    @property
    def source_name(self) -> str:
        """Return the name of the data source."""
        return "producthunt.com"

    @property
    def expected_columns(self) -> List[str]:
        """Return list of expected columns in ProductHunt CSV."""
        return [
            "name",
            "tagline",
            "description",
            "website",
            "maker",
            "launch_date",
            "upvotes",
            "comments_count",
            "pricing",
            "category",
        ]

    def validate_csv_format(self, csv_content: str) -> bool:
        """Validate that CSV has ProductHunt format."""
        try:
            df = pd.read_csv(StringIO(csv_content))

            # Check for required columns
            required_cols = ["name", "tagline"]  # Minimum required
            missing_cols = [col for col in required_cols if col not in df.columns]

            if missing_cols:
                raise ValueError(
                    f"Missing required ProductHunt columns: {missing_cols}. "
                    f"Expected columns: {self.expected_columns}"
                )

            return True

        except Exception as e:
            raise ValueError(f"Invalid ProductHunt CSV format: {str(e)}")

    def get_sample_csv_format(self) -> str:
        """Return sample ProductHunt CSV format."""
        return (
            "# Sample ProductHunt CSV format:\n"
            '"name","tagline","description","website","maker","launch_date",'
            '"upvotes","comments_count","pricing","category"\n'
            '"ChatGPT","AI Assistant","Revolutionary AI chatbot",'
            '"https://openai.com/chatgpt","OpenAI","2022-11-30","1500","250",'
            '"Freemium","AI Tools"'
        )

    def parse_csv_content(self, csv_content: str) -> List[Dict[str, Any]]:
        """
        Parse ProductHunt CSV content and convert to standardized format.

        Args:
            csv_content (str): CSV content as string

        Returns:
            List[Dict]: List of tool dictionaries in standard format
        """
        try:
            # Read CSV with pandas
            df = pd.read_csv(StringIO(csv_content))

            # Clean column names
            df.columns = df.columns.str.strip()

            logger.info(f"Loaded ProductHunt CSV with {len(df)} rows")

            # Filter out rows without names
            df = df[df["name"].notna() & (df["name"].str.strip() != "")]

            tools = []
            for _, row in df.iterrows():
                tool = self._transform_row(row)
                if tool:
                    tools.append(tool)

            logger.info(f"Successfully parsed {len(tools)} ProductHunt tools")
            return tools

        except Exception as e:
            logger.error(f"Error parsing ProductHunt CSV: {e}")
            raise

    def _transform_row(self, row: pd.Series) -> Dict[str, Any] | None:
        """Transform a ProductHunt CSV row into standard tool format."""
        try:
            name = self._clean_string(row.get("name"))
            if not name:
                return None

            return {
                "name": name,
                "slug": self._generate_slug(name),
                "description": self._extract_description(row),
                "website_url": self._clean_url(row.get("website")),
                "logo_url": None,  # ProductHunt CSV might not have logos
                "pricing_type": self._extract_pricing_type(row.get("pricing")),
                "price_range": self._extract_price_range(row.get("pricing")),
                "has_free_trial": self._extract_has_free_trial(row.get("pricing")),
                "tags": self._extract_tags(row),
                "features": self._extract_features(row),
                "quality_score": self._calculate_quality_score(row),
                "popularity_score": self._calculate_popularity_score(row),
                "is_featured": False,
                "source": self.source_name,
            }
        except Exception as e:
            logger.warning(
                f"Error transforming ProductHunt row for {row.get('name', 'unknown')}: {e}"
            )
            return None

    def _clean_string(self, value: Any) -> str | None:
        """Clean and normalize string values."""
        if pd.isna(value):
            return None
        cleaned = str(value).strip()
        return cleaned if cleaned else None

    def _generate_slug(self, name: str) -> str:
        """Generate URL-friendly slug from name."""
        slug = name.lower()
        slug = re.sub(r"[^a-z0-9\s-]", "", slug)
        slug = re.sub(r"\s+", "-", slug)
        slug = re.sub(r"--+", "-", slug)
        slug = slug.strip("-")
        return slug

    def _clean_url(self, url: Any) -> str | None:
        """Clean URL."""
        if pd.isna(url):
            return None
        return str(url).strip()

    def _extract_description(self, row: pd.Series) -> str:
        """Extract description from ProductHunt fields."""
        description = self._clean_string(row.get("description"))
        tagline = self._clean_string(row.get("tagline"))

        if description and len(description) > 10:
            return description
        elif tagline:
            return tagline
        else:
            return f"ProductHunt tool: {tagline or 'No description available'}"

    def _extract_pricing_type(self, pricing_str: Any) -> str:
        """Extract pricing type from ProductHunt pricing field."""
        if pd.isna(pricing_str):
            return "no-pricing"

        pricing = str(pricing_str).lower()

        if "free" in pricing and "paid" not in pricing:
            return "free"
        elif "freemium" in pricing or ("free" in pricing and "paid" in pricing):
            return "freemium"
        elif any(word in pricing for word in ["paid", "$", "subscription", "monthly"]):
            return "paid"
        elif "one-time" in pricing or "lifetime" in pricing:
            return "one-time"

        return "no-pricing"

    def _extract_price_range(self, pricing_str: Any) -> str | None:
        """Extract price range from ProductHunt pricing field."""
        if pd.isna(pricing_str):
            return None
        return str(pricing_str).strip()

    def _extract_has_free_trial(self, pricing_str: Any) -> bool:
        """Check if tool has free trial based on ProductHunt data."""
        if pd.isna(pricing_str):
            return False

        pricing = str(pricing_str).lower()
        return "trial" in pricing or "freemium" in pricing

    def _extract_tags(self, row: pd.Series) -> List[str] | None:
        """Extract tags from ProductHunt data."""
        tags = []

        # Use category as tag
        category = self._clean_string(row.get("category"))
        if category:
            tags.append(category.lower())

        # Add maker as tag
        maker = self._clean_string(row.get("maker"))
        if maker:
            tags.append(f"by-{maker.lower().replace(' ', '-')}")

        return tags if tags else None

    def _extract_features(self, row: pd.Series) -> List[str] | None:
        """Extract features from ProductHunt data."""
        features = []

        # Add features based on upvotes
        upvotes = row.get("upvotes", 0)
        try:
            upvotes = int(upvotes) if not pd.isna(upvotes) else 0
            if upvotes > 500:
                features.append("highly-popular")
            elif upvotes > 100:
                features.append("popular")
        except (ValueError, TypeError):
            pass

        # Add feature based on comments
        comments = row.get("comments_count", 0)
        try:
            comments = int(comments) if not pd.isna(comments) else 0
            if comments > 50:
                features.append("well-discussed")
        except (ValueError, TypeError):
            pass

        return features if features else None

    def _calculate_quality_score(self, row: pd.Series) -> int:
        """Calculate quality score based on ProductHunt metrics."""
        score = 5.0  # Base score

        # Boost based on upvotes
        try:
            upvotes = int(row.get("upvotes", 0)) if not pd.isna(row.get("upvotes")) else 0
            if upvotes > 1000:
                score += 3
            elif upvotes > 500:
                score += 2
            elif upvotes > 100:
                score += 1
        except (ValueError, TypeError):
            pass

        # Boost based on comments (engagement)
        try:
            comments = (
                int(row.get("comments_count", 0)) if not pd.isna(row.get("comments_count")) else 0
            )
            if comments > 100:
                score += 1
            elif comments > 50:
                score += 0.5
        except (ValueError, TypeError):
            pass

        return max(1, min(10, round(score)))

    def _calculate_popularity_score(self, row: pd.Series) -> int:
        """Calculate popularity score based on ProductHunt metrics."""
        score = 0

        # Use upvotes as primary popularity metric
        try:
            upvotes = int(row.get("upvotes", 0)) if not pd.isna(row.get("upvotes")) else 0
            score += upvotes // 10  # 1 point per 10 upvotes
        except (ValueError, TypeError):
            pass

        # Add comment engagement
        try:
            comments = (
                int(row.get("comments_count", 0)) if not pd.isna(row.get("comments_count")) else 0
            )
            score += comments // 5  # 1 point per 5 comments
        except (ValueError, TypeError):
            pass

        return max(0, score)
