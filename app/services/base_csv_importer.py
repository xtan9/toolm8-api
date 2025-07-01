"""Base CSV importer service for bulk tool insertion."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from app.database.connection import db_connection

logger = logging.getLogger(__name__)


class BaseCSVImporter(ABC):
    """Base class for CSV importers from different sources."""

    def __init__(self) -> None:
        self.client = db_connection.get_client()

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the name of the data source (e.g., 'theresanaiforthat.com')."""
        pass

    @abstractmethod
    def get_parser(self) -> Any:
        """Return the appropriate parser for this source."""
        pass

    async def import_from_csv_content(
        self, csv_content: str, replace_existing: bool = False
    ) -> Dict[str, Any]:
        """
        Import tools from CSV content.

        Args:
            csv_content (str): CSV content as string
            replace_existing (bool): Whether to replace existing tools with same slug

        Returns:
            Dict: Import results with counts and details
        """
        try:
            # Get source-specific parser and validate format
            parser = self.get_parser()

            # Validate CSV format before parsing
            parser.validate_csv_format(csv_content)

            # Parse CSV content
            tools = parser.parse_csv_content(csv_content)

            if not tools:
                return {
                    "success": False,
                    "message": f"No valid tools found in {self.source_name} CSV",
                    "imported": 0,
                    "skipped": 0,
                    "errors": 0,
                }

            # Import tools to database
            results = await self.bulk_insert_tools(tools, replace_existing)

            return {
                "success": True,
                "message": f"Successfully processed {len(tools)} tools from {self.source_name}",
                "total_parsed": len(tools),
                "source": self.source_name,
                **results,
            }

        except Exception as e:
            logger.error(f"Error importing {self.source_name} CSV: {e}")
            return {
                "success": False,
                "message": f"Import failed for {self.source_name}: {str(e)}",
                "imported": 0,
                "skipped": 0,
                "errors": 1,
                "source": self.source_name,
            }

    async def bulk_insert_tools(
        self, tools: List[Dict[str, Any]], replace_existing: bool = False
    ) -> Dict[str, int]:
        """
        Bulk insert tools into database using efficient upsert.

        Args:
            tools (List[Dict]): List of tool dictionaries
            replace_existing (bool): Whether to replace existing tools

        Returns:
            Dict: Results with counts
        """
        if not tools:
            return {"imported": 0, "skipped": 0, "errors": 0}

        try:
            if replace_existing:
                # Use upsert to insert or update all tools in one request
                response = self.client.table("tools").upsert(tools, on_conflict="slug").execute()
                imported = len(response.data) if response.data else 0
                logger.info(f"Bulk upserted {imported} tools from {self.source_name}")
                return {"imported": imported, "skipped": 0, "errors": 0}
            else:
                # Get existing slugs in one query to check for conflicts
                existing_slugs = set()
                slugs = [tool["slug"] for tool in tools]

                if slugs:
                    response = (
                        self.client.table("tools").select("slug").in_("slug", slugs).execute()
                    )
                    if response.data:
                        existing_slugs = {row["slug"] for row in response.data}

                # Split tools into new and existing
                new_tools = [tool for tool in tools if tool["slug"] not in existing_slugs]
                skipped_count = len(tools) - len(new_tools)

                if new_tools:
                    # Insert only new tools in one bulk operation
                    response = self.client.table("tools").insert(new_tools).execute()
                    imported = len(response.data) if response.data else 0
                    logger.info(
                        f"Bulk inserted {imported} new tools from {self.source_name}, "
                        f"skipped {skipped_count} existing"
                    )
                else:
                    imported = 0
                    logger.info(f"All {skipped_count} tools from {self.source_name} already exist")

                return {"imported": imported, "skipped": skipped_count, "errors": 0}

        except Exception as e:
            logger.error(f"Error in bulk insert for {self.source_name}: {e}")
            return {"imported": 0, "skipped": 0, "errors": len(tools)}
