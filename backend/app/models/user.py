"""
User model - represents an admin user
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.database import Base


class User(Base):
    """User database model for admin authentication"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=True, nullable=False)  # All users are admins for now
    must_change_password = Column(Boolean, default=True, nullable=False)  # Force password change on first login

    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(TIMESTAMP, nullable=True)

    def __repr__(self):
        return f"<User {self.username} - {self.email}>"
