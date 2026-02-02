"""
Intelligent Merging Activity - Merge PDF pages by category
"""
import logging
from typing import List, Dict
from temporalio import activity, workflow
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import async_session_maker
from app.models import Document

logger = logging.getLogger(__name__)


@activity.defn(name="get_pages_by_category")
async def get_pages_by_category(job_id: str, page_ids: List[str]) -> Dict[str, List[str]]:
    """
    Get all pages grouped by category.

    Args:
        job_id: Job UUID
        page_ids: List of page document IDs

    Returns:
        Dict mapping category names to lists of page document IDs
    """
    activity.heartbeat("Grouping pages by category")

    async with async_session_maker() as db:
        try:
            # Get all pages with category eager loaded, sorted by page number
            result = await db.execute(
                select(Document)
                .options(selectinload(Document.category))
                .where(Document.id.in_(page_ids))
                .order_by(Document.page_number)
            )
            pages = result.scalars().all()

            # Group by category
            by_category = {}
            for page in pages:
                category_name = page.category.name if page.category else "Sonstiges"
                if category_name not in by_category:
                    by_category[category_name] = []
                by_category[category_name].append(str(page.id))

            logger.info(f"Grouped {len(pages)} pages into {len(by_category)} categories")

            return by_category

        except Exception as e:
            logger.error(f"Failed to group pages: {e}")
            raise
