"""
Authentication Schemas
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class LoginRequest(BaseModel):
    """Login request schema"""
    username: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=6)


class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserResponse(BaseModel):
    """User response schema"""
    id: UUID
    username: str
    email: EmailStr
    is_active: bool
    is_admin: bool
    must_change_password: bool = False
    created_at: datetime
    last_login_at: Optional[datetime]

    class Config:
        from_attributes = True


class CurrentUser(BaseModel):
    """Current authenticated user"""
    id: UUID
    username: str
    email: EmailStr
    is_admin: bool
    must_change_password: bool = False

    class Config:
        from_attributes = True


class ChangePasswordRequest(BaseModel):
    """Password change request schema"""
    current_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)


class ChangePasswordResponse(BaseModel):
    """Password change response"""
    message: str
