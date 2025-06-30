from fastapi import APIRouter

router = APIRouter()


@router.get("/stats")
async def get_stats() -> dict[str, str]:
    return {"message": "Admin stats endpoint - implement as needed"}
