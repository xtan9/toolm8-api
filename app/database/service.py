import logging
from typing import List, Optional

from slugify import slugify

from app.database.connection import db_connection
from app.models import Tool, ToolCreate

logger = logging.getLogger(__name__)


class DatabaseService:
    def insert_tool(self, tool: ToolCreate) -> Optional[Tool]:
        client = db_connection.get_client()
        try:
            data = {
                "name": tool.name,
                "slug": tool.slug,
                "description": tool.description,
                "website_url": tool.website_url,
                "logo_url": tool.logo_url,
                "pricing_type": tool.pricing_type,
                "price_range": tool.price_range,
                "has_free_trial": tool.has_free_trial,
                "tags": tool.tags,
                "features": tool.features,
                "quality_score": tool.quality_score,
                "popularity_score": tool.popularity_score,
                "is_featured": tool.is_featured,
                "source": tool.source,
            }

            response = client.table("tools").insert(data).execute()

            if response.data and len(response.data) > 0:
                return Tool(**response.data[0])
            return None
        except Exception as e:
            logger.error(f"Error inserting tool: {e}")
            return None

    def bulk_insert_tools(self, tools: List[ToolCreate]) -> int:
        client = db_connection.get_client()
        inserted_count = 0

        try:
            for tool in tools:
                try:
                    data = {
                        "name": tool.name,
                        "slug": tool.slug,
                        "description": tool.description,
                        "website_url": tool.website_url,
                        "logo_url": tool.logo_url,
                        "pricing_type": tool.pricing_type,
                        "price_range": tool.price_range,
                        "has_free_trial": tool.has_free_trial,
                        "tags": tool.tags,
                        "features": tool.features,
                        "quality_score": tool.quality_score,
                        "popularity_score": tool.popularity_score,
                        "is_featured": tool.is_featured,
                        "source": tool.source,
                    }

                    # Use upsert to handle conflicts
                    response = client.table("tools").upsert(data, on_conflict="slug").execute()

                    if response.data and len(response.data) > 0:
                        inserted_count += 1

                except Exception as e:
                    logger.error(f"Error inserting tool {tool.name}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error in bulk insert: {e}")

        logger.info(f"Bulk inserted {inserted_count} tools")
        return inserted_count

    def get_tools_by_tags(self, tags: List[str], limit: int = 50, offset: int = 0) -> List[Tool]:
        """Get tools that contain any of the specified tags"""
        client = db_connection.get_client()
        try:
            # Use PostgreSQL array overlap operator to find tools with matching tags
            response = (
                client.table("tools")
                .select("*")
                .filter("tags", "cs", f'{{{",".join(tags)}}}')
                .order("popularity_score", desc=True)
                .order("quality_score", desc=True)
                .limit(limit)
                .offset(offset)
                .execute()
            )

            if response.data:
                return [Tool(**item) for item in response.data]
            return []
        except Exception as e:
            logger.error(f"Error getting tools by tags: {e}")
            return []

    def get_all_tools(self, limit: int = 50, offset: int = 0) -> List[Tool]:
        """Get all tools with pagination"""
        client = db_connection.get_client()
        try:
            response = (
                client.table("tools")
                .select("*")
                .order("popularity_score", desc=True)
                .order("quality_score", desc=True)
                .limit(limit)
                .offset(offset)
                .execute()
            )

            if response.data:
                return [Tool(**item) for item in response.data]
            return []
        except Exception as e:
            logger.error(f"Error getting all tools: {e}")
            return []

    def get_featured_tools(self, limit: int = 20) -> List[Tool]:
        """Get featured tools"""
        client = db_connection.get_client()
        try:
            response = (
                client.table("tools")
                .select("*")
                .eq("is_featured", True)
                .order("popularity_score", desc=True)
                .order("quality_score", desc=True)
                .limit(limit)
                .execute()
            )

            if response.data:
                return [Tool(**item) for item in response.data]
            return []
        except Exception as e:
            logger.error(f"Error getting featured tools: {e}")
            return []

    def search_tools(self, query: str, limit: int = 50, offset: int = 0) -> List[Tool]:
        """Search tools by name and description"""
        client = db_connection.get_client()
        try:
            # Search by name first
            name_response = (
                client.table("tools")
                .select("*")
                .filter("name", "ilike", f"%{query}%")
                .order("popularity_score", desc=True)
                .order("quality_score", desc=True)
                .limit(limit)
                .offset(offset)
                .execute()
            )

            # Search by description
            desc_response = (
                client.table("tools")
                .select("*")
                .filter("description", "ilike", f"%{query}%")
                .order("popularity_score", desc=True)
                .order("quality_score", desc=True)
                .limit(limit)
                .offset(offset)
                .execute()
            )

            # Combine and deduplicate results
            tools = []
            seen_ids = set()

            if name_response.data:
                for item in name_response.data:
                    if item["id"] not in seen_ids:
                        tools.append(Tool(**item))
                        seen_ids.add(item["id"])

            if desc_response.data:
                for item in desc_response.data:
                    if item["id"] not in seen_ids:
                        tools.append(Tool(**item))
                        seen_ids.add(item["id"])

            # Sort by popularity and quality score
            tools.sort(key=lambda x: (-x.popularity_score, -x.quality_score))
            return tools[:limit]

        except Exception as e:
            logger.error(f"Error searching tools: {e}")
            return []

    def get_all_tags(self) -> List[str]:
        """Get all unique tags from all tools"""
        client = db_connection.get_client()
        try:
            response = client.table("tools").select("tags").execute()

            if response.data:
                all_tags = set()
                for row in response.data:
                    if row.get("tags"):
                        all_tags.update(row["tags"])
                return sorted(list(all_tags))
            return []
        except Exception as e:
            logger.error(f"Error getting all tags: {e}")
            return []

    def check_duplicate_tool(
        self,
        name: Optional[str] = None,
        website_url: Optional[str] = None,
        slug: Optional[str] = None,
    ) -> bool:
        client = db_connection.get_client()
        try:
            query = client.table("tools").select("id")

            filters_applied = False

            if name:
                query = query.ilike("name", name)
                filters_applied = True

            if website_url:
                if filters_applied:
                    # For OR condition, we need to do separate queries
                    url_query = client.table("tools").select("id").eq("website_url", website_url)
                    url_response = url_query.execute()
                    if url_response.data and len(url_response.data) > 0:
                        return True
                else:
                    query = query.eq("website_url", website_url)
                    filters_applied = True

            if slug:
                if filters_applied:
                    # For OR condition, check slug separately
                    slug_query = client.table("tools").select("id").eq("slug", slug)
                    slug_response = slug_query.execute()
                    if slug_response.data and len(slug_response.data) > 0:
                        return True
                else:
                    query = query.eq("slug", slug)
                    filters_applied = True

            if not filters_applied:
                return False

            response = query.execute()
            return bool(response.data and len(response.data) > 0)

        except Exception as e:
            logger.error(f"Error checking duplicate tool: {e}")
            return False

    def generate_slug(self, text: str) -> str:
        result = slugify(text, lowercase=True, max_length=200)
        return str(result)


db_service = DatabaseService()
