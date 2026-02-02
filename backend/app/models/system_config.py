"""
System Config model - key-value configuration store
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, TIMESTAMP, Boolean

from app.database import Base


class SystemConfig(Base):
    """System Configuration database model"""
    __tablename__ = "system_config"

    key = Column(String(255), primary_key=True)
    value = Column(Text, nullable=False)
    value_type = Column(String(50), nullable=False, default="string")  # string, integer, boolean, json

    description = Column(Text, nullable=True)
    is_secret = Column(Boolean, default=False)

    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<SystemConfig {self.key}>"
