"""
Categorization response schemas for structured LLM outputs
"""
from pydantic import BaseModel, Field


class CategorizationResponse(BaseModel):
    """Response schema for document categorization (Flow 1)"""
    category: str = Field(..., description="Exact category name from available categories")
    new_filename: str = Field(..., description="Descriptive filename without extension")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0 and 1")


class PageCategorizationResponse(BaseModel):
    """Response schema for page categorization (Flow 2)"""
    category: str = Field(..., description="Exact category name from available categories")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0 and 1")
