"""
Job Status Update Activities
"""
import logging
from datetime import datetime
from temporalio import activity
from sqlalchemy import update
from app.database import async_session_maker
from app.models.job import Job

logger = logging.getLogger(__name__)


@activity.defn(name="update_job_status_to_failed")
async def update_job_status_to_failed(job_id: str, error_message: str) -> None:
    """
    Update job status to failed with error message.
    Uses update() statement to avoid loading large blobs into memory.

    Args:
        job_id: Job UUID
        error_message: Error message to store
    """
    async with async_session_maker() as db:
        try:
            result = await db.execute(
                update(Job)
                .where(Job.id == job_id)
                .values(
                    status="failed",
                    error_message=error_message[:1000],
                    processing_completed_at=datetime.utcnow()
                )
            )

            if result.rowcount == 0:
                logger.error(f"Job {job_id} not found")
                return

            await db.commit()
            logger.info(f"Job {job_id} marked as failed: {error_message}")

        except Exception as e:
            logger.error(f"Failed to update job status: {e}")
            await db.rollback()
            raise
