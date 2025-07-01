import logging
import re
import urllib.parse
from typing import Any, Dict, List, Optional

import pandas as pd


class TAaftParser:
    def __init__(self) -> None:
        self.source = "theresanaiforthat.com"
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def parse_csv(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse CSV file and convert to database-ready format

        Args:
            file_path (str): Path to the CSV file

        Returns:
            List[Dict]: List of tool dictionaries ready for database insertion
        """
        try:
            # Read CSV with pandas
            df = pd.read_csv(file_path)

            # Clean column names (remove extra spaces)
            df.columns = df.columns.str.strip()

            self.logger.info(f"Loaded CSV with {len(df)} rows and {len(df.columns)} columns")

            # Filter out rows without tool names
            df = df[df["ai_link"].notna() & (df["ai_link"].str.strip() != "")]

            tools = []
            for _, row in df.iterrows():
                tool = self.transform_row(row)
                if tool:
                    tools.append(tool)

            self.logger.info(f"Successfully parsed {len(tools)} tools from CSV")
            return tools

        except Exception as e:
            self.logger.error(f"Error parsing CSV: {e}")
            raise

    def transform_row(self, row: pd.Series) -> Optional[Dict[str, Any]]:
        """
        Transform a CSV row into a database tool object

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
            self.logger.warning(f"Error transforming row for {row.get('ai_link', 'unknown')}: {e}")
            return None

    def clean_string(self, value: Any) -> Optional[str]:
        """Clean and normalize string values"""
        if pd.isna(value) or not isinstance(value, str):
            return None
        cleaned = str(value).strip()
        return cleaned if cleaned else None

    def generate_slug(self, name: str) -> str:
        """Generate URL-friendly slug from name"""
        slug = name.lower()
        slug = re.sub(r"[^a-z0-9\s-]", "", slug)  # Remove special characters
        slug = re.sub(r"\s+", "-", slug)  # Replace spaces with hyphens
        slug = re.sub(r"--+", "-", slug)  # Replace multiple hyphens
        slug = slug.strip("-")  # Remove leading/trailing hyphens
        return slug

    def clean_url(self, url: Any) -> Optional[str]:
        """Clean URL by removing tracking parameters"""
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
            self.logger.warning(f"Invalid URL: {url}")
            return None

    def extract_description(self, row: pd.Series) -> Optional[str]:
        """Extract description from available fields"""
        task_label = self.clean_string(row.get("task_label"))
        comment_body = self.clean_string(row.get("comment_body"))

        if comment_body and len(comment_body) > 10:
            prefix = f"{task_label}. " if task_label else ""
            return f"{prefix}{comment_body}"

        return task_label or f"AI tool for {task_label or 'various tasks'}"

    def extract_pricing_type(self, pricing_str: Any) -> str:
        """Extract pricing type from pricing string"""
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
        """Extract price range from pricing string"""
        if pd.isna(pricing_str) or not isinstance(pricing_str, str):
            return None

        # Clean up pricing string for display
        cleaned = re.sub(r"^(Free \+ )?from \$", "$", pricing_str, flags=re.IGNORECASE)
        cleaned = re.sub(r"\/mo$", "/month", cleaned)
        return cleaned

    def extract_has_free_trial(self, pricing_str: Any) -> bool:
        """Check if tool has free trial"""
        if pd.isna(pricing_str) or not isinstance(pricing_str, str):
            return False

        pricing = pricing_str.lower()
        return "free" in pricing or "trial" in pricing

    def extract_tags(self, row: pd.Series) -> Optional[List[str]]:
        """Extract tags from task label"""
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
        """Extract features based on available data"""
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
        """Calculate quality score based on available metrics"""
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
        """Calculate popularity score based on views and saves"""
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

    def generate_insert_sql(self, tools: List[Dict[str, Any]]) -> str:
        """Generate SQL INSERT statements"""
        if not tools:
            return ""

        def escape_sql_string(value: Any) -> str:
            if value is None:
                return "NULL"
            return f"'{str(value).replace(chr(39), chr(39) + chr(39))}'"

        def format_array(arr: Any) -> str:
            if not arr:
                return "NULL"
            escaped_items = [escape_sql_string(item)[1:-1] for item in arr]  # Remove quotes
            quoted_items = [f"'{item}'" for item in escaped_items]
            return f"ARRAY[{','.join(quoted_items)}]"

        values = []
        for tool in tools:
            value_parts = [
                escape_sql_string(tool.get("name")),
                escape_sql_string(tool.get("slug")),
                escape_sql_string(tool.get("description")),
                escape_sql_string(tool.get("website_url")),
                escape_sql_string(tool.get("logo_url")),
                escape_sql_string(tool.get("pricing_type")),
                escape_sql_string(tool.get("price_range")),
                "TRUE" if tool.get("has_free_trial") is True else "FALSE",
                format_array(tool.get("tags", [])),
                format_array(tool.get("features", [])),
                str(tool.get("quality_score", 1)),
                str(tool.get("popularity_score", 0)),
                "TRUE" if tool.get("is_featured") is True else "FALSE",
                escape_sql_string(tool.get("source")),
            ]
            values.append(f"({','.join(value_parts)})")

        columns = [
            "name",
            "slug",
            "description",
            "website_url",
            "logo_url",
            "pricing_type",
            "price_range",
            "has_free_trial",
            "tags",
            "features",
            "quality_score",
            "popularity_score",
            "is_featured",
            "source",
        ]

        sql = f"""
        INSERT INTO tools ({','.join(columns)})
        VALUES {','.join(values)}
        ON CONFLICT (slug) DO UPDATE SET
            name = EXCLUDED.name,
            description = EXCLUDED.description,
            website_url = EXCLUDED.website_url,
            logo_url = EXCLUDED.logo_url,
            pricing_type = EXCLUDED.pricing_type,
            price_range = EXCLUDED.price_range,
            has_free_trial = EXCLUDED.has_free_trial,
            tags = EXCLUDED.tags,
            features = EXCLUDED.features,
            quality_score = EXCLUDED.quality_score,
            popularity_score = EXCLUDED.popularity_score,
            is_featured = EXCLUDED.is_featured,
            source = EXCLUDED.source;
        """

        return sql
