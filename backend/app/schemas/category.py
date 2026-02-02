"""
Category API Schemas
"""
from typing import Optional
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class CategoryBase(BaseModel):
    """Base category schema"""
    name: str
    description: Optional[str] = None
    color: Optional[str] = None
    display_order: int = 0
    is_active: bool = True


class CategoryCreate(CategoryBase):
    """Schema for creating category"""
    pass


class CategoryUpdate(BaseModel):
    """Schema for updating category"""
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


class CategoryResponse(CategoryBase):
    """Category response schema"""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
