"""TAAFT CSV import service for bulk tool insertion."""

import logging

from app.services.base_csv_importer import BaseCSVImporter
from app.services.csv_parser import TAaftCSVParser

logger = logging.getLogger(__name__)


class TAaftCSVImporter(BaseCSVImporter):
    """Service for importing tools from TheResAnAIForThat.com CSV data."""

    def __init__(self) -> None:
        super().__init__()
        self.parser = TAaftCSVParser()

    @property
    def source_name(self) -> str:
        """Return the name of the data source."""
        return "theresanaiforthat.com"

    def get_parser(self) -> TAaftCSVParser:
        """Return the TAAFT-specific parser."""
        return self.parser
