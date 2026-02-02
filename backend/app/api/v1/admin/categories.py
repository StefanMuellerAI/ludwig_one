"""
Admin API - Categories Management
"""
import logging
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_db
from app.models import Category
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.auth import require_admin, get_current_user
from app.schemas.auth import CurrentUser
from app.utils.audit import log_admin_action

logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("", response_model=List[CategoryResponse])
@limiter.limit("100/minute")
async def list_categories(
    request: Request,
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    List all categories.

    Args:
        include_inactive: Include inactive categories
        db: Database session

    Returns:
        List of categories
    """
    try:
        query = select(Category).order_by(Category.display_order, Category.name)

        if not include_inactive:
            query = query.where(Category.is_active == True)

        result = await db.execute(query)
        categories = result.scalars().all()

        return [CategoryResponse.model_validate(cat) for cat in categories]

    except Exception as e:
        logger.error(f"Category listing failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("", response_model=CategoryResponse)
async def create_category(
    category: CategoryCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create new category.

    Args:
        category: Category data
        db: Database session

    Returns:
        Created category
    """
    try:
        # Check if name already exists
        result = await db.execute(
            select(Category).where(Category.name == category.name)
        )
        existing = result.scalar_one_or_none()

        if existing:
            raise HTTPException(status_code=400, detail="Category name already exists")

        # Create category
        new_category = Category(**category.model_dump())
        db.add(new_category)
        await db.commit()
        await db.refresh(new_category)

        logger.info(f"Created category: {new_category.name}")

        return CategoryResponse.model_validate(new_category)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Category creation failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get category by ID.

    Args:
        category_id: Category UUID
        db: Database session

    Returns:
        Category details
    """
    try:
        result = await db.execute(
            select(Category).where(Category.id == category_id)
        )
        category = result.scalar_one_or_none()

        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

        return CategoryResponse.model_validate(category)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Category retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: UUID,
    category_update: CategoryUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update category.

    Args:
        category_id: Category UUID
        category_update: Update data
        db: Database session

    Returns:
        Updated category
    """
    try:
        result = await db.execute(
            select(Category).where(Category.id == category_id)
        )
        category = result.scalar_one_or_none()

        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

        # Update fields
        update_data = category_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(category, field, value)

        await db.commit()
        await db.refresh(category)

        logger.info(f"Updated category: {category.name}")

        return CategoryResponse.model_validate(category)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Category update failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{category_id}")
async def delete_category(
    category_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete category.

    Args:
        category_id: Category UUID
        db: Database session

    Returns:
        Success message
    """
    try:
        result = await db.execute(
            select(Category).where(Category.id == category_id)
        )
        category = result.scalar_one_or_none()

        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

        await db.delete(category)
        await db.commit()

        logger.info(f"Deleted category: {category.name}")

        return {"message": "Category deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Category deletion failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
