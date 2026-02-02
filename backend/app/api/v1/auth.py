"""
Authentication API Endpoints
"""
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_db
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse, CurrentUser, ChangePasswordRequest, ChangePasswordResponse
from app.auth import verify_password, create_access_token, get_current_user, get_password_hash
from app.config import settings
from app.utils.audit import log_admin_action

logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with username and password.

    Args:
        credentials: Login credentials
        db: Database session

    Returns:
        JWT access token
    """
    try:
        # Get user by username
        result = await db.execute(
            select(User).where(User.username == credentials.username)
        )
        user = result.scalar_one_or_none()

        # Check if user exists and password is correct
        if not user or not verify_password(credentials.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )

        # Update last login time
        user.last_login_at = datetime.utcnow()
        await db.commit()

        # Log successful login
        await log_admin_action(
            db=db,
            user=CurrentUser(
                id=user.id,
                username=user.username,
                email=user.email,
                is_admin=user.is_admin,
                must_change_password=user.must_change_password
            ),
            action="LOGIN",
            resource_type="auth",
            description=f"User {user.username} logged in",
            request=request
        )

        # Create access token
        access_token = create_access_token(
            data={"sub": str(user.id), "username": user.username}
        )

        logger.info(f"User {user.username} logged in successfully")

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.jwt_access_token_expire_minutes * 60
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user information.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        User details
    """
    try:
        result = await db.execute(
            select(User).where(User.id == current_user.id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return UserResponse.model_validate(user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )


@router.post("/change-password", response_model=ChangePasswordResponse)
@limiter.limit("5/hour")
async def change_password(
    request: Request,
    password_data: ChangePasswordRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Change user password.

    Args:
        request: FastAPI request
        password_data: Password change data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Success message
    """
    try:
        # Validate passwords match
        if password_data.new_password != password_data.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New passwords do not match"
            )

        # Get user from database
        result = await db.execute(
            select(User).where(User.id == current_user.id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Verify current password
        if not verify_password(password_data.current_password, user.hashed_password):
            # Log failed attempt
            await log_admin_action(
                db=db,
                user=current_user,
                action="CHANGE_PASSWORD",
                resource_type="auth",
                description="Failed password change - incorrect current password",
                request=request,
                success="failed",
                error_message="Incorrect current password"
            )

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect"
            )

        # Prevent reusing same password
        if verify_password(password_data.new_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from current password"
            )

        # Update password
        user.hashed_password = get_password_hash(password_data.new_password)
        user.must_change_password = False
        await db.commit()

        # Log successful password change
        await log_admin_action(
            db=db,
            user=current_user,
            action="CHANGE_PASSWORD",
            resource_type="auth",
            description=f"User {current_user.username} changed password",
            request=request
        )

        logger.info(f"User {current_user.username} changed password successfully")

        return ChangePasswordResponse(
            message="Password changed successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
