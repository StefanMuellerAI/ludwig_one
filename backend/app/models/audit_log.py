"""
Audit Log Model - tracks admin actions
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, TIMESTAMP, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.database import Base


class AuditLog(Base):
    """Audit log for admin actions"""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Who performed the action
    user_id = Column(UUID(as_uuid=True), nullable=False)
    username = Column(String(255), nullable=False)

    # What action was performed
    action = Column(String(100), nullable=False)  # CREATE, UPDATE, DELETE, LOGIN, LOGOUT, etc.
    resource_type = Column(String(100), nullable=False)  # user, category, prompt, config, job
    resource_id = Column(String(255), nullable=True)  # ID of affected resource

    # Details
    description = Column(Text, nullable=True)
    changes = Column(JSON, nullable=True)  # Store what changed (before/after)

    # Request metadata
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    endpoint = Column(String(255), nullable=True)
    method = Column(String(10), nullable=True)  # GET, POST, PUT, DELETE

    # Status
    success = Column(String(20), nullable=False, default="success")  # success, failed
    error_message = Column(Text, nullable=True)

    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<AuditLog {self.username} - {self.action} {self.resource_type}>"
