import logging
from typing import List, Optional

from slugify import slugify

from app.database.connection import db_connection
from app.models import Category, CategoryCreate, Tool, ToolCreate

logger = logging.getLogger(__name__)


class DatabaseService:
    def insert_category(self, category: CategoryCreate) -> Optional[Category]:
        client = db_connection.get_client()
        try:
            data = {
                "name": category.name,
                "slug": category.slug,
                "description": category.description,
                "display_order": category.display_order,
                "is_featured": category.is_featured,
            }

            response = client.table("categories").insert(data).execute()

            if response.data and len(response.data) > 0:
                return Category(**response.data[0])
            return None
        except Exception as e:
            logger.error(f"Error inserting category: {e}")
            return None

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
                "category_id": tool.category_id,
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
                        "category_id": tool.category_id,
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

    def get_tools_by_category(
        self, category_id: int, limit: int = 50, offset: int = 0
    ) -> List[Tool]:
        client = db_connection.get_client()
        try:
            response = (
                client.table("tools")
                .select("*")
                .eq("category_id", category_id)
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
            logger.error(f"Error getting tools by category: {e}")
            return []

    def check_duplicate_tool(
        self, name: str = None, website_url: str = None, slug: str = None
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

    def get_all_categories(self) -> List[Category]:
        client = db_connection.get_client()
        try:
            response = (
                client.table("categories")
                .select("*")
                .order("display_order")
                .order("name")
                .execute()
            )

            if response.data:
                return [Category(**item) for item in response.data]
            return []
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return []

    def find_category_by_name(self, name: str) -> Optional[Category]:
        client = db_connection.get_client()
        try:
            response = client.table("categories").select("*").ilike("name", name).execute()

            if response.data and len(response.data) > 0:
                return Category(**response.data[0])
            return None
        except Exception as e:
            logger.error(f"Error finding category by name: {e}")
            return None

    def generate_slug(self, text: str) -> str:
        return slugify(text, lowercase=True, max_length=200)


db_service = DatabaseService()
