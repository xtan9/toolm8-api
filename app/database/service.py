import asyncpg
from typing import List, Optional, Dict, Any
from app.models import Category, CategoryCreate, Tool, ToolCreate, ToolClick, ToolClickCreate
from app.database.connection import db_connection
import logging
import slugify

logger = logging.getLogger(__name__)

class DatabaseService:
    
    async def insert_category(self, category: CategoryCreate) -> Optional[Category]:
        pool = await db_connection.get_pool()
        try:
            async with pool.acquire() as conn:
                query = """
                    INSERT INTO categories (name, slug, description, display_order, is_featured)
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING id, name, slug, description, display_order, is_featured, created_at, updated_at
                """
                row = await conn.fetchrow(
                    query,
                    category.name,
                    category.slug,
                    category.description,
                    category.display_order,
                    category.is_featured
                )
                if row:
                    return Category(**dict(row))
                return None
        except Exception as e:
            logger.error(f"Error inserting category: {e}")
            return None
    
    async def insert_tool(self, tool: ToolCreate) -> Optional[Tool]:
        pool = await db_connection.get_pool()
        try:
            async with pool.acquire() as conn:
                query = """
                    INSERT INTO tools (
                        name, slug, description, website_url, logo_url, pricing_type,
                        price_range, has_free_trial, category_id, tags, features,
                        quality_score, popularity_score, is_featured, source
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                    RETURNING id, name, slug, description, website_url, logo_url, pricing_type,
                              price_range, has_free_trial, category_id, tags, features,
                              quality_score, popularity_score, is_featured, click_count,
                              source, created_at, updated_at
                """
                row = await conn.fetchrow(
                    query,
                    tool.name,
                    tool.slug,
                    tool.description,
                    tool.website_url,
                    tool.logo_url,
                    tool.pricing_type,
                    tool.price_range,
                    tool.has_free_trial,
                    tool.category_id,
                    tool.tags,
                    tool.features,
                    tool.quality_score,
                    tool.popularity_score,
                    tool.is_featured,
                    tool.source
                )
                if row:
                    return Tool(**dict(row))
                return None
        except Exception as e:
            logger.error(f"Error inserting tool: {e}")
            return None
    
    async def bulk_insert_tools(self, tools: List[ToolCreate]) -> int:
        pool = await db_connection.get_pool()
        inserted_count = 0
        
        try:
            async with pool.acquire() as conn:
                async with conn.transaction():
                    for tool in tools:
                        try:
                            query = """
                                INSERT INTO tools (
                                    name, slug, description, website_url, logo_url, pricing_type,
                                    price_range, has_free_trial, category_id, tags, features,
                                    quality_score, popularity_score, is_featured, source
                                )
                                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                                ON CONFLICT (slug) DO NOTHING
                            """
                            result = await conn.execute(
                                query,
                                tool.name,
                                tool.slug,
                                tool.description,
                                tool.website_url,
                                tool.logo_url,
                                tool.pricing_type,
                                tool.price_range,
                                tool.has_free_trial,
                                tool.category_id,
                                tool.tags,
                                tool.features,
                                tool.quality_score,
                                tool.popularity_score,
                                tool.is_featured,
                                tool.source
                            )
                            if "INSERT" in result:
                                inserted_count += 1
                        except Exception as e:
                            logger.error(f"Error inserting tool {tool.name}: {e}")
                            continue
                            
        except Exception as e:
            logger.error(f"Error in bulk insert: {e}")
            
        logger.info(f"Bulk inserted {inserted_count} tools")
        return inserted_count
    
    async def get_tools_by_category(self, category_id: int, limit: int = 50, offset: int = 0) -> List[Tool]:
        pool = await db_connection.get_pool()
        try:
            async with pool.acquire() as conn:
                query = """
                    SELECT id, name, slug, description, website_url, logo_url, pricing_type,
                           price_range, has_free_trial, category_id, tags, features,
                           quality_score, popularity_score, is_featured, click_count,
                           source, created_at, updated_at
                    FROM tools
                    WHERE category_id = $1
                    ORDER BY popularity_score DESC, quality_score DESC
                    LIMIT $2 OFFSET $3
                """
                rows = await conn.fetch(query, category_id, limit, offset)
                return [Tool(**dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Error getting tools by category: {e}")
            return []
    
    async def check_duplicate_tool(self, name: str = None, website_url: str = None, slug: str = None) -> bool:
        pool = await db_connection.get_pool()
        try:
            async with pool.acquire() as conn:
                conditions = []
                params = []
                param_count = 0
                
                if name:
                    param_count += 1
                    conditions.append(f"LOWER(name) = LOWER(${param_count})")
                    params.append(name)
                
                if website_url:
                    param_count += 1
                    conditions.append(f"website_url = ${param_count}")
                    params.append(website_url)
                
                if slug:
                    param_count += 1
                    conditions.append(f"slug = ${param_count}")
                    params.append(slug)
                
                if not conditions:
                    return False
                
                query = f"SELECT EXISTS(SELECT 1 FROM tools WHERE {' OR '.join(conditions)})"
                result = await conn.fetchval(query, *params)
                return result
        except Exception as e:
            logger.error(f"Error checking duplicate tool: {e}")
            return False
    
    async def get_all_categories(self) -> List[Category]:
        pool = await db_connection.get_pool()
        try:
            async with pool.acquire() as conn:
                query = """
                    SELECT id, name, slug, description, display_order, is_featured, created_at, updated_at
                    FROM categories
                    ORDER BY display_order ASC, name ASC
                """
                rows = await conn.fetch(query)
                return [Category(**dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return []
    
    async def find_category_by_name(self, name: str) -> Optional[Category]:
        pool = await db_connection.get_pool()
        try:
            async with pool.acquire() as conn:
                query = """
                    SELECT id, name, slug, description, display_order, is_featured, created_at, updated_at
                    FROM categories
                    WHERE LOWER(name) = LOWER($1)
                """
                row = await conn.fetchrow(query, name)
                if row:
                    return Category(**dict(row))
                return None
        except Exception as e:
            logger.error(f"Error finding category by name: {e}")
            return None
    
    async def record_tool_click(self, click: ToolClickCreate) -> Optional[ToolClick]:
        pool = await db_connection.get_pool()
        try:
            async with pool.acquire() as conn:
                async with conn.transaction():
                    # Insert click record
                    click_query = """
                        INSERT INTO tool_clicks (tool_id, ip_address)
                        VALUES ($1, $2)
                        RETURNING id, tool_id, clicked_at, ip_address
                    """
                    click_row = await conn.fetchrow(click_query, click.tool_id, click.ip_address)
                    
                    # Update tool click count
                    update_query = """
                        UPDATE tools 
                        SET click_count = click_count + 1,
                            popularity_score = popularity_score + 1
                        WHERE id = $1
                    """
                    await conn.execute(update_query, click.tool_id)
                    
                    if click_row:
                        return ToolClick(**dict(click_row))
                    return None
        except Exception as e:
            logger.error(f"Error recording tool click: {e}")
            return None

    def generate_slug(self, text: str) -> str:
        return slugify.slugify(text, lowercase=True, max_length=200)

db_service = DatabaseService()