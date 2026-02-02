"""
Prompt Template model - represents LLM prompt templates
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, TIMESTAMP, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.database import Base


class PromptTemplate(Base):
    """Prompt Template database model"""
    __tablename__ = "prompt_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name = Column(String(255), nullable=False, unique=True)
    purpose = Column(String(100), nullable=False)  # vision_extraction, categorization_flow1, etc.

    template = Column(Text, nullable=False)

    # Model config
    model_name = Column(String(100), nullable=False, default="mistral-large-latest")
    temperature = Column(Float, default=0.1)
    max_tokens = Column(Integer, default=4096)
    token_limit = Column(Integer, nullable=True)  # For chunking (insight_generation only)

    # Version control
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)

    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<PromptTemplate {self.name} v{self.version}>"
