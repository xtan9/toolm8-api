"""CSV parser service for theresanaiforthat.com scraping results."""

import logging
import re
import urllib.parse
from io import StringIO
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class TAaftCSVParser:
    """Parser for theresanaiforthat.com CSV scraping results."""

    def __init__(self) -> None:
        self.source = "theresanaiforthat.com"

    def parse_csv_content(self, csv_content: str) -> List[Dict[str, Any]]:
        """
        Parse CSV content and convert to database-ready format.

        Args:
            csv_content (str): CSV content as string

        Returns:
            List[Dict]: List of tool dictionaries ready for database insertion
        """
        try:
            # Read CSV from string content
            df = pd.read_csv(StringIO(csv_content))

            # Clean column names (remove extra spaces)
            df.columns = df.columns.str.strip()

            logger.info(f"Loaded CSV with {len(df)} rows and {len(df.columns)} columns")

            # Filter out rows without tool names
            df = df[df["ai_link"].notna() & (df["ai_link"].str.strip() != "")]

            tools = []
            for idx, row in df.iterrows():
                tool = self.transform_row(row)
                if tool:
                    tools.append(tool)

            logger.info(f"Successfully parsed {len(tools)} tools from CSV")
            return tools

        except Exception as e:
            logger.error(f"Error parsing CSV: {e}")
            raise

    def transform_row(self, row: pd.Series) -> Optional[Dict[str, Any]]:
        """
        Transform a CSV row into a database tool object.

        Args:
            row (pd.Series): CSV row

        Returns:
            Dict or None: Database-ready tool object or None if invalid
        """
        try:
            name = self.clean_string(row.get("ai_link"))
            if not name:
                return None

            return {
                "name": name,
                "slug": self.generate_slug(name),
                "description": self.extract_description(row),
                "website_url": self.clean_url(
                    row.get("external_ai_link href") or row.get("visit_ai_website_link href")
                ),
                "logo_url": self.clean_string(row.get("taaft_icon src")),
                "pricing_type": self.extract_pricing_type(row.get("ai_launch_date")),
                "price_range": self.extract_price_range(row.get("ai_launch_date")),
                "has_free_trial": self.extract_has_free_trial(row.get("ai_launch_date")),
                "tags": self.extract_tags(row),
                "features": self.extract_features(row),
                "quality_score": self.calculate_quality_score(row),
                "popularity_score": self.calculate_popularity_score(row),
                "is_featured": False,  # Default to False
                "click_count": 0,  # Default to 0
                "source": self.source,
            }
        except Exception as e:
            logger.warning(f"Error transforming row for {row.get('ai_link', 'unknown')}: {e}")
            return None

    def clean_string(self, value: Any) -> Optional[str]:
        """Clean and normalize string values."""
        if pd.isna(value) or not isinstance(value, str):
            return None
        cleaned = str(value).strip()
        return cleaned if cleaned else None

    def generate_slug(self, name: str) -> str:
        """Generate URL-friendly slug from name."""
        slug = name.lower()
        slug = re.sub(r"[^a-z0-9\s-]", "", slug)  # Remove special characters
        slug = re.sub(r"\s+", "-", slug)  # Replace spaces with hyphens
        slug = re.sub(r"--+", "-", slug)  # Replace multiple hyphens
        slug = slug.strip("-")  # Remove leading/trailing hyphens
        return slug

    def clean_url(self, url: Any) -> Optional[str]:
        """Clean URL by removing tracking parameters."""
        if pd.isna(url) or not isinstance(url, str):
            return None

        try:
            parsed = urllib.parse.urlparse(url)

            # Remove tracking parameters
            query_params = urllib.parse.parse_qs(parsed.query)
            tracking_params = [
                "ref",
                "utm_source",
                "utm_medium",
                "utm_campaign",
                "utm_content",
                "utm_term",
            ]

            for param in tracking_params:
                query_params.pop(param, None)

            # Rebuild URL
            clean_query = urllib.parse.urlencode(query_params, doseq=True)
            clean_parsed = parsed._replace(query=clean_query)

            return urllib.parse.urlunparse(clean_parsed)
        except Exception:
            logger.warning(f"Invalid URL: {url}")
            return None

    def extract_description(self, row: pd.Series) -> Optional[str]:
        """Extract description from available fields."""
        task_label = self.clean_string(row.get("task_label"))
        comment_body = self.clean_string(row.get("comment_body"))

        if comment_body and len(comment_body) > 10:
            prefix = f"{task_label}. " if task_label else ""
            return f"{prefix}{comment_body}"

        return task_label or f"AI tool for {task_label or 'various tasks'}"

    def extract_pricing_type(self, pricing_str: Any) -> str:
        """Extract pricing type from pricing string."""
        if pd.isna(pricing_str) or not isinstance(pricing_str, str):
            return "no-pricing"

        pricing = pricing_str.lower()

        if "100% free" in pricing or pricing == "free":
            return "free"
        elif "free +" in pricing or "free trial" in pricing:
            return "freemium"
        elif "from $" in pricing or "/mo" in pricing:
            return "paid"
        elif "one-time" in pricing or "buy once" in pricing:
            return "one-time"

        return "no-pricing"

    def extract_price_range(self, pricing_str: Any) -> Optional[str]:
        """Extract price range from pricing string."""
        if pd.isna(pricing_str) or not isinstance(pricing_str, str):
            return None

        # Clean up pricing string for display
        cleaned = re.sub(r"^(Free \+ )?from \$", "$", pricing_str, flags=re.IGNORECASE)
        cleaned = re.sub(r"\/mo$", "/month", cleaned)
        return cleaned

    def extract_has_free_trial(self, pricing_str: Any) -> bool:
        """Check if tool has free trial."""
        if pd.isna(pricing_str) or not isinstance(pricing_str, str):
            return False

        pricing = pricing_str.lower()
        return "free" in pricing or "trial" in pricing

    def extract_tags(self, row: pd.Series) -> Optional[List[str]]:
        """Extract tags from task label."""
        tags = []

        task_label = self.clean_string(row.get("task_label"))
        if task_label:
            tags.append(task_label.lower())

        # Add pricing-based tags
        pricing_type = self.extract_pricing_type(row.get("ai_launch_date"))
        if pricing_type == "free":
            tags.append("free")
        elif pricing_type == "freemium":
            tags.append("freemium")

        return tags if tags else None

    def extract_features(self, row: pd.Series) -> Optional[List[str]]:
        """Extract features based on available data."""
        features = []

        # Add features based on rating
        if not pd.isna(row.get("average_rating")):
            try:
                rating = float(row["average_rating"])
                if rating >= 4.5:
                    features.append("highly-rated")
            except (ValueError, TypeError):
                pass

        # Add feature if has user reviews
        if self.clean_string(row.get("comment_body")):
            features.append("user-reviewed")

        return features if features else None

    def calculate_quality_score(self, row: pd.Series) -> int:
        """Calculate quality score based on available metrics."""
        score = 5.0  # Base score

        # Boost based on rating
        if not pd.isna(row.get("average_rating")):
            try:
                rating = float(row["average_rating"])
                if rating >= 4.5:
                    score += 2
                elif rating >= 4.0:
                    score += 1
                elif rating < 3.0:
                    score -= 1
            except (ValueError, TypeError):
                pass

        # Boost if has user comments
        if self.clean_string(row.get("comment_body")):
            score += 1

        # Boost based on saves
        try:
            saves = int(row.get("saves", 0))
            if saves > 50:
                score += 1
            elif saves > 20:
                score += 0.5
        except (ValueError, TypeError):
            pass

        return max(1, min(10, round(score)))

    def calculate_popularity_score(self, row: pd.Series) -> int:
        """Calculate popularity score based on views and saves."""
        score = 0

        # Parse views
        try:
            views_str = str(row.get("stats_views", "0")).replace(",", "")
            views = int(views_str)
            score += views // 1000
        except (ValueError, TypeError):
            pass

        # Parse saves
        try:
            saves = int(row.get("saves", 0))
            score += saves * 2
        except (ValueError, TypeError):
            pass

        return max(0, score)
