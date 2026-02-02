"""
Merge decision schema for PDF page merging (Flow 2)
"""
from pydantic import BaseModel, Field


class MergeDecision(BaseModel):
    """Response schema for merge decision between two documents"""
    should_merge: bool = Field(..., description="Whether documents should be merged together")
    reasoning: str = Field(..., description="Brief explanation of the decision")
