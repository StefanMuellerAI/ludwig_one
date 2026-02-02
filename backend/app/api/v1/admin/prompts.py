"""
Admin API - Prompt Templates Management
"""
import logging
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import PromptTemplate
from app.schemas.prompt_template import PromptTemplateCreate, PromptTemplateUpdate, PromptTemplateResponse
from app.auth import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("", response_model=List[PromptTemplateResponse])
async def list_prompts(
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    List all prompt templates.

    Args:
        include_inactive: Include inactive templates
        db: Database session

    Returns:
        List of prompt templates
    """
    try:
        query = select(PromptTemplate).order_by(PromptTemplate.purpose, PromptTemplate.name)

        if not include_inactive:
            query = query.where(PromptTemplate.is_active == True)

        result = await db.execute(query)
        prompts = result.scalars().all()

        return [PromptTemplateResponse.model_validate(p) for p in prompts]

    except Exception as e:
        logger.error(f"Prompt listing failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("", response_model=PromptTemplateResponse)
async def create_prompt(
    prompt: PromptTemplateCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create new prompt template.

    Args:
        prompt: Prompt template data
        db: Database session

    Returns:
        Created prompt template
    """
    try:
        # Check if purpose already exists
        result = await db.execute(
            select(PromptTemplate).where(PromptTemplate.purpose == prompt.purpose)
        )
        existing = result.scalar_one_or_none()

        if existing:
            raise HTTPException(status_code=400, detail="Prompt with this purpose already exists")

        # Create prompt
        new_prompt = PromptTemplate(**prompt.model_dump())
        db.add(new_prompt)
        await db.commit()
        await db.refresh(new_prompt)

        logger.info(f"Created prompt template: {new_prompt.name}")

        return PromptTemplateResponse.model_validate(new_prompt)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Prompt creation failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{prompt_id}", response_model=PromptTemplateResponse)
async def get_prompt(
    prompt_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get prompt template by ID.

    Args:
        prompt_id: Prompt UUID
        db: Database session

    Returns:
        Prompt template details
    """
    try:
        result = await db.execute(
            select(PromptTemplate).where(PromptTemplate.id == prompt_id)
        )
        prompt = result.scalar_one_or_none()

        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt template not found")

        return PromptTemplateResponse.model_validate(prompt)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prompt retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{prompt_id}", response_model=PromptTemplateResponse)
async def update_prompt(
    prompt_id: UUID,
    prompt_update: PromptTemplateUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update prompt template.

    Args:
        prompt_id: Prompt UUID
        prompt_update: Update data
        db: Database session

    Returns:
        Updated prompt template
    """
    try:
        result = await db.execute(
            select(PromptTemplate).where(PromptTemplate.id == prompt_id)
        )
        prompt = result.scalar_one_or_none()

        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt template not found")

        # Update fields
        update_data = prompt_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(prompt, field, value)

        await db.commit()
        await db.refresh(prompt)

        logger.info(f"Updated prompt template: {prompt.name}")

        return PromptTemplateResponse.model_validate(prompt)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Prompt update failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{prompt_id}")
async def delete_prompt(
    prompt_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete prompt template.

    Args:
        prompt_id: Prompt UUID
        db: Database session

    Returns:
        Success message
    """
    try:
        result = await db.execute(
            select(PromptTemplate).where(PromptTemplate.id == prompt_id)
        )
        prompt = result.scalar_one_or_none()

        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt template not found")

        await db.delete(prompt)
        await db.commit()

        logger.info(f"Deleted prompt template: {prompt.name}")

        return {"message": "Prompt template deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Prompt deletion failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
