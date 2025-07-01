"""ProductHunt CSV import service - EXAMPLE implementation."""

from app.services.base_csv_importer import BaseCSVImporter
from app.services.producthunt_csv_parser import ProductHuntCSVParser


class ProductHuntCSVImporter(BaseCSVImporter):
    """Service for importing tools from ProductHunt CSV data."""

    def __init__(self) -> None:
        super().__init__()
        self.parser = ProductHuntCSVParser()

    @property
    def source_name(self) -> str:
        """Return the name of the data source."""
        return "producthunt.com"

    def get_parser(self) -> ProductHuntCSVParser:
        """Return the ProductHunt-specific parser."""
        return self.parser
