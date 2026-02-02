"""
Job API Schemas
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID


class JobResponse(BaseModel):
    """Job response schema"""
    id: UUID
    type: str
    status: str
    workflow_id: Optional[str] = None

    total_files: int
    processed_files: int
    failed_files: int

    original_filename: str
    output_archive_path: Optional[str] = None

    error_message: Optional[str] = None
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    """List of jobs"""
    jobs: list[JobResponse]
    total: int


class JobCreateResponse(BaseModel):
    """Response after creating a job"""
    job_id: UUID
    message: str
