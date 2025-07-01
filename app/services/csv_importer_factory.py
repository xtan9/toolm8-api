"""Factory for creating CSV importers for different sources."""

import logging
from typing import Dict, Type

from app.services.base_csv_importer import BaseCSVImporter
from app.services.taaft_csv_importer import TAaftCSVImporter

logger = logging.getLogger(__name__)


class CSVImporterFactory:
    """Factory for creating CSV importers based on source type."""

    _importers: Dict[str, Type[BaseCSVImporter]] = {
        "taaft": TAaftCSVImporter,
        "theresanaiforthat": TAaftCSVImporter,  # Alias
        "theresanaiforthat.com": TAaftCSVImporter,  # Alias
    }

    @classmethod
    def get_importer(cls, source: str) -> BaseCSVImporter:
        """
        Get CSV importer for the specified source.

        Args:
            source (str): Source identifier (e.g., 'taaft', 'theresanaiforthat')

        Returns:
            BaseCSVImporter: Appropriate CSV importer instance

        Raises:
            ValueError: If source is not supported
        """
        source_key = source.lower().strip()

        if source_key not in cls._importers:
            available_sources = ", ".join(cls._importers.keys())
            raise ValueError(
                f"Unsupported source '{source}'. Available sources: {available_sources}"
            )

        importer_class = cls._importers[source_key]
        return importer_class()

    @classmethod
    def register_importer(cls, source: str, importer_class: Type[BaseCSVImporter]) -> None:
        """
        Register a new CSV importer for a source.

        Args:
            source (str): Source identifier
            importer_class: Class that inherits from BaseCSVImporter
        """
        if not issubclass(importer_class, BaseCSVImporter):
            raise ValueError("Importer class must inherit from BaseCSVImporter")

        cls._importers[source.lower().strip()] = importer_class
        logger.info(f"Registered CSV importer for source: {source}")

    @classmethod
    def get_supported_sources(cls) -> list[str]:
        """Get list of supported source identifiers."""
        return list(cls._importers.keys())

    @classmethod
    def is_source_supported(cls, source: str) -> bool:
        """Check if a source is supported."""
        return source.lower().strip() in cls._importers
