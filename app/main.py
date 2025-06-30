import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.database.connection import db_connection
from app.routers import admin, health

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

app.include_router(health.router, tags=["health"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
