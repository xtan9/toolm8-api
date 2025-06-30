from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def root() -> dict[str, str]:
    return {"message": "ToolM8 Data Management API - AI Tools Scraping Service"}


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy", "service": "toolm8-data-api"}
