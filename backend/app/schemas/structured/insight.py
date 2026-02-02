"""
Insight generation schema for job summary
"""
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class InsightData(BaseModel):
    """Response schema for insight generation"""
    applicant_name: Optional[str] = Field(None, description="Name of applicant if identifiable")
    application_numbers: List[str] = Field(default_factory=list, description="List of application/case numbers found")
    key_findings: List[str] = Field(default_factory=list, description="Important findings or themes")
    categories_summary: Dict[str, int] = Field(default_factory=dict, description="Count of documents per category")
    important_dates: List[str] = Field(default_factory=list, description="Important dates or deadlines")
    total_documents: int = Field(..., description="Total number of documents processed")
    total_pages: Optional[int] = Field(None, description="Total number of pages if applicable")
