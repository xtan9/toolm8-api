from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import asyncio
import logging

from app.models import Tool, Category, ToolClickCreate
from app.database.service import db_service
from app.database.connection import db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ToolM8 API",
    description="AI Tools Directory API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting ToolM8 API...")
    try:
        await db_connection.get_pool()
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down ToolM8 API...")
    await db_connection.close_pool()

@app.get("/")
async def root():
    return {"message": "ToolM8 API - AI Tools Directory"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "toolm8-api"}

@app.get("/categories", response_model=List[Category])
async def get_categories():
    try:
        categories = await db_service.get_all_categories()
        return categories
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/categories/{category_id}/tools", response_model=List[Tool])
async def get_tools_by_category(
    category_id: int,
    limit: int = 50,
    offset: int = 0
):
    try:
        tools = await db_service.get_tools_by_category(category_id, limit, offset)
        return tools
    except Exception as e:
        logger.error(f"Error getting tools by category: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/tools/{tool_id}/click")
async def record_tool_click(tool_id: int, ip_address: Optional[str] = None):
    try:
        click_data = ToolClickCreate(tool_id=tool_id, ip_address=ip_address)
        result = await db_service.record_tool_click(click_data)
        if result:
            return {"message": "Click recorded successfully"}
        else:
            raise HTTPException(status_code=404, detail="Tool not found")
    except Exception as e:
        logger.error(f"Error recording click: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)