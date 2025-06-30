import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, Optional

from fastapi import FastAPI, HTTPException

from app.database.connection import db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
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
async def root() -> dict[str, str]:
    return {"message": "ToolM8 Data Management API - AI Tools Scraping Service"}


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy", "service": "toolm8-data-api"}


@app.get("/admin/stats")
async def get_database_stats() -> dict[str, Any]:
    """Get database statistics"""
    try:
        client = db_connection.get_client()

        # Get categories count
        categories_response = (
            client.table("categories")
            .select("id", count="exact")  # type: ignore[arg-type]
            .execute()
        )
        categories_count = categories_response.count or 0

        # Get tools count
        tools_response = (
            client.table("tools").select("id", count="exact").execute()  # type: ignore[arg-type]
        )
        tools_count = tools_response.count or 0

        # Get recent tools (last 24 hours)
        from datetime import datetime, timedelta

        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        recent_response = (
            client.table("tools")
            .select("id", count="exact")  # type: ignore[arg-type]
            .gte("created_at", yesterday)
            .execute()
        )
        recent_tools = recent_response.count or 0

        # Get tools by source
        sources_response = client.table("tools").select("source").execute()
        source_counts: Dict[str, int] = {}
        if sources_response.data:
            for row in sources_response.data:
                source = row.get("source", "unknown")
                source_counts[source] = source_counts.get(source, 0) + 1

        sources = [{"source": k, "count": v} for k, v in source_counts.items()]
        sources.sort(key=lambda x: x["count"], reverse=True)  # type: ignore[arg-type,return-value]

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
async def clear_tools(source: Optional[str] = None) -> dict[str, Any]:
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
