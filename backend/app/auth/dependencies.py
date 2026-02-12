"""
Authentication dependencies for route protection
"""
from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.auth.utils import decode_access_token
from app.schemas.auth import CurrentUser
from app.config import settings


# HTTP Bearer token scheme
security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)

async def _load_user_from_token(token: str, db: AsyncSession) -> CurrentUser:
    """Load and validate a user from a JWT token."""
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: Optional[str] = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    return CurrentUser(
        id=user.id,
        username=user.username,
        email=user.email,
        is_admin=user.is_admin,
        must_change_password=user.must_change_password
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> CurrentUser:
    """
    Get current authenticated user from JWT token.
    """
    return await _load_user_from_token(credentials.credentials, db)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
    db: AsyncSession = Depends(get_db)
) -> Optional[CurrentUser]:
    """Return user if a valid token is present, otherwise None."""
    if credentials is None:
        return None
    return await _load_user_from_token(credentials.credentials, db)


async def require_admin(
    current_user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """
    Require admin privileges.

    Args:
        current_user: Current authenticated user

    Returns:
        Current user if admin

    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.must_change_password:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Password change required"
        )

    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )

    return current_user


async def require_job_access(
    request: Request,
    current_user: Optional[CurrentUser] = Depends(get_optional_user)
) -> None:
    """
    Allow access if:
    - A valid JWT user is present, OR
    - A valid API key is provided (for email download links), OR
    - No API key is provided (access controlled by Nginx Basic Auth)
    """
    if current_user:
        return

    # If an API key is provided, validate it (for email links)
    api_key = request.headers.get("x-api-key") or request.query_params.get("api_key")
    if api_key and api_key != settings.job_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )

    # Allow access -- Nginx Basic Auth protects the endpoints externally
    return
