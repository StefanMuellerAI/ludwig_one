"""
Audit Logging Utilities
"""
import logging
from typing import Optional, Dict, Any
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.schemas.auth import CurrentUser

logger = logging.getLogger(__name__)


async def log_admin_action(
    db: AsyncSession,
    user: CurrentUser,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    description: Optional[str] = None,
    changes: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None,
    success: str = "success",
    error_message: Optional[str] = None
):
    """
    Log an admin action to the audit log.

    Args:
        db: Database session
        user: Current authenticated user
        action: Action performed (CREATE, UPDATE, DELETE, LOGIN, etc.)
        resource_type: Type of resource (user, category, prompt, config, job)
        resource_id: ID of the affected resource
        description: Human-readable description
        changes: Dictionary of changes (before/after values)
        request: FastAPI Request object (for IP, user agent, endpoint)
        success: Status (success, failed)
        error_message: Error message if failed
    """
    try:
        # Extract request metadata
        ip_address = None
        user_agent = None
        endpoint = None
        method = None

        if request:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")
            endpoint = str(request.url.path)
            method = request.method

        # Create audit log entry
        audit_log = AuditLog(
            user_id=user.id,
            username=user.username,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
            endpoint=endpoint,
            method=method,
            success=success,
            error_message=error_message
        )

        db.add(audit_log)
        await db.commit()

        logger.info(
            f"Audit: {user.username} {action} {resource_type} "
            f"{resource_id or ''} - {success}"
        )

    except Exception as e:
        logger.error(f"Failed to create audit log: {e}")
        # Don't fail the actual operation if audit logging fails
        pass
