"""
Document model - represents a single document in a job
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, TIMESTAMP, Float, Boolean, ForeignKey, LargeBinary
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.database import Base


class Document(Base):
    """Document database model"""
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)

    # Original file info
    original_filename = Column(String(512), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size_bytes = Column(Integer, nullable=True)
    original_blob = Column(LargeBinary, nullable=False)

    # PDF page info (for Flow 2)
    page_number = Column(Integer, nullable=True)
    total_pages = Column(Integer, nullable=True)

    # Categorization results
    assigned_category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    assigned_filename = Column(String(512), nullable=True)
    categorization_confidence = Column(Float, nullable=True)

    # Merging info (Flow 2)
    merged_into_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    is_merged_parent = Column(Boolean, default=False)

    # Token usage
    total_tokens = Column(Integer, default=0)

    # Status
    processing_status = Column(String(50), default="pending")
    error_message = Column(Text, nullable=True)

    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    job = relationship("Job", back_populates="documents")
    category = relationship("Category", back_populates="documents")
    extractions = relationship("Extraction", back_populates="document", cascade="all, delete-orphan")

    # Self-referential for merging
    merged_into = relationship("Document", remote_side=[id], foreign_keys=[merged_into_id])

    def __repr__(self):
        return f"<Document {self.id} - {self.original_filename}>"
