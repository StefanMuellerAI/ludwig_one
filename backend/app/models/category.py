"""
Category model - represents document categories
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, TIMESTAMP, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.database import Base


class Category(Base):
    """Category database model"""
    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)  # Hex color code

    # Ordering
    display_order = Column(Integer, default=0)

    is_active = Column(Boolean, default=True)

    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    documents = relationship("Document", back_populates="category")

    def __repr__(self):
        return f"<Category {self.name}>"
