"""
Filename generation schema for merged documents (Flow 2)
"""
from pydantic import BaseModel, Field


class FilenameGenerationResponse(BaseModel):
    """Response schema for filename generation"""
    new_filename: str = Field(..., description="Descriptive filename without extension")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0 and 1")
