"""
System Config API Schemas
"""
from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class SystemConfigBase(BaseModel):
    """Base config schema"""
    key: str
    value: str
    value_type: str = "string"
    description: Optional[str] = None
    is_secret: bool = False


class SystemConfigCreate(SystemConfigBase):
    """Schema for creating config"""
    pass


class SystemConfigUpdate(BaseModel):
    """Schema for updating config"""
    value: Optional[str] = None
    value_type: Optional[str] = None
    description: Optional[str] = None
    is_secret: Optional[bool] = None


class SystemConfigResponse(SystemConfigBase):
    """Config response schema"""
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SystemConfigValueResponse(BaseModel):
    """Simple value response"""
    key: str
    value: str
    value_type: str
