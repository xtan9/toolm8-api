from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class CategoryBase(BaseModel):
    name: str = Field(..., max_length=100)
    slug: str = Field(..., max_length=100)
    description: Optional[str] = None
    display_order: int = 0
    is_featured: bool = False


class CategoryCreate(CategoryBase):
    pass


class Category(CategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ToolBase(BaseModel):
    name: str = Field(..., max_length=200)
    slug: str = Field(..., max_length=200)
    description: Optional[str] = None
    website_url: Optional[str] = Field(None, max_length=500)
    logo_url: Optional[str] = Field(None, max_length=500)
    pricing_type: Optional[str] = Field(None, regex="^(free|freemium|paid|one-time)$")
    price_range: Optional[str] = Field(None, max_length=100)
    has_free_trial: bool = False
    category_id: Optional[int] = None
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
