import logging
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, FastAPI, HTTPException

from app.database.connection import db_connection
from app.database.seed import seed_categories
from app.database.service import db_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup logic
    logger.info("Starting ToolM8 Data Management API...")
    try:
        db_connection.get_client()
        logger.info("Supabase client initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")

    yield

    # Shutdown logic
    logger.info("Shutting down ToolM8 Data Management API...")


app = FastAPI(
    title="ToolM8 Data Management API",
    description="AI Tools Data Scraping and Management Service",
    version="1.0.0",
    lifespan=lifespan,
)


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
        client = db_connection.get_client()

        # Get categories count
        categories_response = client.table("categories").select("id", count="exact").execute()
        categories_count = categories_response.count or 0

        # Get tools count
        tools_response = client.table("tools").select("id", count="exact").execute()
        tools_count = tools_response.count or 0

        # Get recent tools (last 24 hours)
        from datetime import datetime, timedelta

        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        recent_response = (
            client.table("tools").select("id", count="exact").gte("created_at", yesterday).execute()
        )
        recent_tools = recent_response.count or 0

        # Get tools by source
        sources_response = client.table("tools").select("source").execute()
        source_counts = {}
        if sources_response.data:
            for row in sources_response.data:
                source = row.get("source", "unknown")
                source_counts[source] = source_counts.get(source, 0) + 1

        sources = [{"source": k, "count": v} for k, v in source_counts.items()]
        sources.sort(key=lambda x: x["count"], reverse=True)

        return {
            "categories_count": categories_count,
            "tools_count": tools_count,
            "recent_tools_24h": recent_tools,
            "sources": sources,
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get stats")


@app.delete("/admin/clear-tools")
async def clear_tools(source: str = None):
    """Clear tools from database, optionally by source"""
    try:
        client = db_connection.get_client()

        if source:
            response = client.table("tools").delete().eq("source", source).execute()
            message = f"Cleared tools from source: {source}"
        else:
            response = client.table("tools").delete().neq("id", 0).execute()  # Delete all
            message = "Cleared all tools"

        rows_affected = len(response.data) if response.data else 0
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
                inserted_count = db_service.bulk_insert_tools(tools)
                logger.info(f"Successfully inserted {inserted_count} tools")
            else:
                logger.warning("No tools scraped")

    except Exception as e:
        logger.error(f"Scraper task failed: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
