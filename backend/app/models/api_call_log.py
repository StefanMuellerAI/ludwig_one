"""
API Call Log model - tracks all LLM API calls
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, TIMESTAMP, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.database import Base


class APICallLog(Base):
    """API Call Log database model"""
    __tablename__ = "api_call_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    extraction_id = Column(UUID(as_uuid=True), ForeignKey("extractions.id", ondelete="SET NULL"), nullable=True)

    # Call details
    api_provider = Column(String(50), nullable=False)  # mistral, ollama
    model_name = Column(String(100), nullable=False)
    call_type = Column(String(50), nullable=False)  # vision, text_completion, structured_output

    # Request
    prompt_text = Column(Text, nullable=True)
    prompt_tokens = Column(Integer, nullable=True)
    image_count = Column(Integer, default=0)

    # Response
    response_text = Column(Text, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)

    # Performance
    duration_ms = Column(Integer, nullable=True)
    retry_attempt = Column(Integer, default=0)

    # Status
    success = Column(Boolean, nullable=False)
    error_message = Column(Text, nullable=True)

    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<APICallLog {self.id} - {self.api_provider}/{self.call_type}>"
