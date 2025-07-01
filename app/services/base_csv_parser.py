"""Base CSV parser interface for different data sources."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseCSVParser(ABC):
    """Abstract base class for CSV parsers from different sources."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the name of the data source (e.g., 'theresanaiforthat.com')."""
        pass

    @property
    @abstractmethod
    def expected_columns(self) -> List[str]:
        """Return list of expected/required columns in the CSV."""
        pass

    @abstractmethod
    def parse_csv_content(self, csv_content: str) -> List[Dict[str, Any]]:
        """
        Parse CSV content and convert to standardized tool format.

        Args:
            csv_content (str): Raw CSV content as string

        Returns:
            List[Dict]: List of tool dictionaries in standard format:
            {
                "name": str,
                "slug": str,
                "description": str,
                "website_url": Optional[str],
                "logo_url": Optional[str],
                "pricing_type": str,  # "free", "paid", "freemium", "one-time", "no-pricing"
                "price_range": Optional[str],
                "has_free_trial": bool,
                "tags": Optional[List[str]],
                "features": Optional[List[str]],
                "quality_score": int,  # 1-10
                "popularity_score": int,
                "is_featured": bool,
                "source": str
            }
        """
        pass

    @abstractmethod
    def validate_csv_format(self, csv_content: str) -> bool:
        """
        Validate that the CSV has the expected format for this source.

        Args:
            csv_content (str): CSV content to validate

        Returns:
            bool: True if format is valid for this source

        Raises:
            ValueError: If format is invalid with descriptive message
        """
        pass

    def get_sample_csv_format(self) -> str:
        """
        Return a sample CSV header showing expected format.
        Override in subclasses to provide source-specific examples.
        """
        return (
            f"# Sample CSV format for {self.source_name}\n"
            "# Override get_sample_csv_format() in subclass"
        )
