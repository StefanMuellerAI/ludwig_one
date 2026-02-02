"""
Extraction model - represents extracted content from a document
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, TIMESTAMP, ForeignKey, Enum as SQLEnum, LargeBinary
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum

from app.database import Base


class ExtractionType(str, enum.Enum):
    """Extraction type enumeration"""
    TEXT = "text"
    VISION = "vision"
    OCR = "ocr"


class Extraction(Base):
    """Extraction database model"""
    __tablename__ = "extractions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)

    extraction_type = Column(SQLEnum(ExtractionType, name="extraction_type", values_callable=lambda obj: [e.value for e in obj]), nullable=False)

    # Content
    content = Column(Text, nullable=True)
    image_blob = Column(LargeBinary, nullable=True)

    # Metadata
    token_count = Column(Integer, default=0)
    model_used = Column(String(100), nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    retry_count = Column(Integer, default=0)

    # Status
    extraction_status = Column(String(50), default="pending")
    error_message = Column(Text, nullable=True)

    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="extractions")

    def __repr__(self):
        return f"<Extraction {self.id} - {self.extraction_type.value}>"
