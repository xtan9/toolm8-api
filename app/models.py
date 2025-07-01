from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ToolBase(BaseModel):
    name: str = Field(..., max_length=200)
    slug: str = Field(..., max_length=200)
    description: Optional[str] = None
    website_url: Optional[str] = Field(None, max_length=500)
    logo_url: Optional[str] = Field(None, max_length=500)
    pricing_type: Optional[str] = Field(None, pattern="^(free|freemium|paid|one-time)$")
    price_range: Optional[str] = Field(None, max_length=100)
    has_free_trial: bool = False
    tags: List[str] = []
    features: List[str] = []
    quality_score: int = Field(5, ge=1, le=10)
    popularity_score: int = 0
    is_featured: bool = False
    source: Optional[str] = Field(None, max_length=100)


class ToolCreate(ToolBase):
    pass


class Tool(ToolBase):
    id: int
    click_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CSVImportResponse(BaseModel):
    """Response model for CSV import operations."""

    success: bool
    message: str
    total_parsed: Optional[int] = None
    imported: int = 0
    skipped: int = 0
    errors: int = 0
