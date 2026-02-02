"""
Job model - represents a document processing job
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, TIMESTAMP, Enum as SQLEnum, LargeBinary
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum

from app.database import Base


class JobType(str, enum.Enum):
    """Job type enumeration"""
    TAR_PROCESSING = "tar_processing"
    PDF_SPLITTING = "pdf_splitting"


class JobStatus(str, enum.Enum):
    """Job status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Job(Base):
    """Job database model"""
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(SQLEnum(JobType, name="job_type", values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    status = Column(SQLEnum(JobStatus, name="job_status", values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=JobStatus.PENDING)
    workflow_id = Column(String(255), nullable=True)

    # Progress tracking
    total_files = Column(Integer, default=0)
    processed_files = Column(Integer, default=0)
    failed_files = Column(Integer, default=0)

    # Original upload
    original_filename = Column(String(512), nullable=False)
    original_blob = Column(LargeBinary, nullable=False)

    # Output
    output_archive_path = Column(String(512), nullable=True)
    output_archive_blob = Column(LargeBinary, nullable=True)
    insight_xml = Column(Text, nullable=True)

    # Metadata
    error_message = Column(Text, nullable=True)
    processing_started_at = Column(TIMESTAMP, nullable=True)
    processing_completed_at = Column(TIMESTAMP, nullable=True)

    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    documents = relationship("Document", back_populates="job", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Job {self.id} - {self.type.value} - {self.status.value}>"
