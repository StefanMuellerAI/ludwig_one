"""
Admin API - System Configuration
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import SystemConfig
from app.schemas.config import (
    SystemConfigCreate,
    SystemConfigUpdate,
    SystemConfigResponse,
    SystemConfigValueResponse
)
from app.auth import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("", response_model=List[SystemConfigResponse])
async def list_config(
    include_secrets: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    List all configuration entries.

    Args:
        include_secrets: Include secret values (masked if False)
        db: Database session

    Returns:
        List of config entries
    """
    try:
        result = await db.execute(
            select(SystemConfig).order_by(SystemConfig.key)
        )
        configs = result.scalars().all()

        response = []
        for config in configs:
            config_dict = SystemConfigResponse.model_validate(config).model_dump()

            # Mask secrets if not explicitly requested
            if config.is_secret and not include_secrets:
                config_dict["value"] = "***MASKED***"

            response.append(SystemConfigResponse(**config_dict))

        return response

    except Exception as e:
        logger.error(f"Config listing failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{key}", response_model=SystemConfigValueResponse)
async def get_config_value(
    key: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get configuration value by key.

    Args:
        key: Config key
        db: Database session

    Returns:
        Config value
    """
    try:
        result = await db.execute(
            select(SystemConfig).where(SystemConfig.key == key)
        )
        config = result.scalar_one_or_none()

        if not config:
            raise HTTPException(status_code=404, detail="Config key not found")

        # Mask secret value
        value = "***MASKED***" if config.is_secret else config.value

        return SystemConfigValueResponse(
            key=config.key,
            value=value,
            value_type=config.value_type
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Config retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{key}", response_model=SystemConfigResponse)
async def update_config(
    key: str,
    config_update: SystemConfigUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update configuration value.

    Args:
        key: Config key
        config_update: Update data
        db: Database session

    Returns:
        Updated config
    """
    try:
        result = await db.execute(
            select(SystemConfig).where(SystemConfig.key == key)
        )
        config = result.scalar_one_or_none()

        if not config:
            raise HTTPException(status_code=404, detail="Config key not found")

        # Update fields
        update_data = config_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(config, field, value)

        await db.commit()
        await db.refresh(config)

        logger.info(f"Updated config: {config.key}")

        # Return masked response
        response_dict = SystemConfigResponse.model_validate(config).model_dump()
        if config.is_secret:
            response_dict["value"] = "***MASKED***"

        return SystemConfigResponse(**response_dict)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Config update failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("", response_model=SystemConfigResponse)
async def create_config(
    config: SystemConfigCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create new configuration entry.

    Args:
        config: Config data
        db: Database session

    Returns:
        Created config
    """
    try:
        # Check if key already exists
        result = await db.execute(
            select(SystemConfig).where(SystemConfig.key == config.key)
        )
        existing = result.scalar_one_or_none()

        if existing:
            raise HTTPException(status_code=400, detail="Config key already exists")

        # Create config
        new_config = SystemConfig(**config.model_dump())
        db.add(new_config)
        await db.commit()
        await db.refresh(new_config)

        logger.info(f"Created config: {new_config.key}")

        # Return masked response
        response_dict = SystemConfigResponse.model_validate(new_config).model_dump()
        if new_config.is_secret:
            response_dict["value"] = "***MASKED***"

        return SystemConfigResponse(**response_dict)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Config creation failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
