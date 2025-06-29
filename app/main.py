from fastapi import FastAPI, HTTPException, BackgroundTasks
from typing import Dict, Any
import asyncio
import logging

from app.database.service import db_service
from app.database.connection import db_connection
from app.database.seed import seed_categories
from app.scraper.theresanaiforthat import run_scraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ToolM8 Data Management API",
    description="AI Tools Data Scraping and Management Service",
    version="1.0.0",
)


@app.on_event("startup")
async def startup_event():
    logger.info("Starting ToolM8 Data Management API...")
    try:
        await db_connection.get_pool()
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down ToolM8 Data Management API...")
    await db_connection.close_pool()


@app.get("/")
async def root():
    return {"message": "ToolM8 Data Management API - AI Tools Scraping Service"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "toolm8-data-api"}


@app.post("/admin/seed-categories")
async def seed_categories_endpoint(background_tasks: BackgroundTasks):
    """Seed the database with initial categories"""
    try:
        background_tasks.add_task(seed_categories)
        return {"message": "Category seeding started in background"}
    except Exception as e:
        logger.error(f"Error starting category seeding: {e}")
        raise HTTPException(status_code=500, detail="Failed to start seeding")


@app.post("/admin/scrape-tools")
async def scrape_tools_endpoint(background_tasks: BackgroundTasks, max_pages: int = 10):
    """Start scraping tools from theresanaiforthat.com"""
    try:
        background_tasks.add_task(run_scraper_task, max_pages)
        return {"message": f"Scraping started for {max_pages} pages in background"}
    except Exception as e:
        logger.error(f"Error starting scraper: {e}")
        raise HTTPException(status_code=500, detail="Failed to start scraping")


@app.get("/admin/stats")
async def get_database_stats():
    """Get database statistics"""
    try:
        pool = await db_connection.get_pool()
        async with pool.acquire() as conn:
            categories_count = await conn.fetchval("SELECT COUNT(*) FROM categories")
            tools_count = await conn.fetchval("SELECT COUNT(*) FROM tools")

            # Recent tools
            recent_tools = await conn.fetchval(
                "SELECT COUNT(*) FROM tools WHERE created_at > NOW() - INTERVAL '24 hours'"
            )

            # Tools by source
            source_stats = await conn.fetch(
                "SELECT source, COUNT(*) as count FROM tools GROUP BY source ORDER BY count DESC"
            )

            return {
                "categories_count": categories_count,
                "tools_count": tools_count,
                "recent_tools_24h": recent_tools,
                "sources": [
                    {"source": row["source"], "count": row["count"]} for row in source_stats
                ],
            }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get stats")


@app.delete("/admin/clear-tools")
async def clear_tools(source: str = None):
    """Clear tools from database, optionally by source"""
    try:
        pool = await db_connection.get_pool()
        async with pool.acquire() as conn:
            if source:
                result = await conn.execute("DELETE FROM tools WHERE source = $1", source)
                message = f"Cleared tools from source: {source}"
            else:
                result = await conn.execute("DELETE FROM tools")
                message = "Cleared all tools"

            rows_affected = int(result.split()[-1])
            return {"message": message, "rows_deleted": rows_affected}
    except Exception as e:
        logger.error(f"Error clearing tools: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear tools")


async def run_scraper_task(max_pages: int = 10):
    """Background task to run the scraper"""
    try:
        logger.info(f"Starting scraper task with max_pages={max_pages}")
        from app.scraper.theresanaiforthat import TheresAnAIForThatScraper

        async with TheresAnAIForThatScraper() as scraper:
            tools = await scraper.scrape_all_tools(max_pages=max_pages)

            if tools:
                logger.info(f"Inserting {len(tools)} tools into database...")
                inserted_count = await db_service.bulk_insert_tools(tools)
                logger.info(f"Successfully inserted {inserted_count} tools")
            else:
                logger.warning("No tools scraped")

    except Exception as e:
        logger.error(f"Scraper task failed: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
