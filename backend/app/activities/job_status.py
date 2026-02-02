"""
Job Status Update Activities
"""
import logging
from datetime import datetime
from temporalio import activity
from sqlalchemy import select
from app.database import async_session_maker
from app.models.job import Job

logger = logging.getLogger(__name__)


@activity.defn(name="update_job_status_to_failed")
async def update_job_status_to_failed(job_id: str, error_message: str) -> None:
    """
    Update job status to failed with error message.

    Args:
        job_id: Job UUID
        error_message: Error message to store
    """
    async with async_session_maker() as db:
        try:
            # Get job
            result = await db.execute(
                select(Job).where(Job.id == job_id)
            )
            job = result.scalar_one_or_none()

            if not job:
                logger.error(f"Job {job_id} not found")
                return

            # Update status
            job.status = "failed"
            job.error_message = error_message[:1000]  # Limit error message length
            job.processing_completed_at = datetime.utcnow()

            await db.commit()
            logger.info(f"Job {job_id} marked as failed: {error_message}")

        except Exception as e:
            logger.error(f"Failed to update job status: {e}")
            await db.rollback()
            raise
