"""
Prompt Template Schemas
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class PromptTemplateBase(BaseModel):
    """Base prompt template schema"""
    name: str = Field(..., max_length=255)
    purpose: str = Field(..., max_length=100)
    template: str
    model_name: str = Field(default="mistral-large-latest", max_length=100)
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1, le=128000)
    token_limit: Optional[int] = Field(default=None, ge=1000, le=200000, description="Token limit for chunking (insight_generation only)")
    is_active: bool = Field(default=True)


class PromptTemplateCreate(PromptTemplateBase):
    """Schema for creating prompt template"""
    pass


class PromptTemplateUpdate(BaseModel):
    """Schema for updating prompt template"""
    name: Optional[str] = Field(None, max_length=255)
    purpose: Optional[str] = Field(None, max_length=100)
    template: Optional[str] = None
    model_name: Optional[str] = Field(None, max_length=100)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1, le=128000)
    token_limit: Optional[int] = Field(None, ge=1000, le=200000)
    is_active: Optional[bool] = None


class PromptTemplateResponse(PromptTemplateBase):
    """Schema for prompt template response"""
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
