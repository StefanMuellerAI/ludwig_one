"""
Email Notification Activity
"""
import logging
from typing import Dict, Any, Optional
from temporalio import activity
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.models import Job, SystemConfig
from app.services.email_service import email_service
from app.config import settings

logger = logging.getLogger(__name__)


@activity.defn(name="send_job_completion_email")
async def send_job_completion_email(job_id: str, error_message: Optional[str] = None) -> Dict[str, Any]:
    """
    Send email notification for completed or failed job.

    Args:
        job_id: Job UUID
        error_message: Optional error message if job failed

    Returns:
        Dict with send result
    """
    activity.heartbeat("Sending email notification")

    async with async_session_maker() as db:
        try:
            # Get job
            result = await db.execute(
                select(Job).where(Job.id == job_id)
            )
            job = result.scalar_one_or_none()

            if not job:
                raise ValueError(f"Job {job_id} not found")

            # Get recipient email from config (or use default)
            config_result = await db.execute(
                select(SystemConfig).where(SystemConfig.key == "recipient_email")
            )
            config = config_result.scalar_one_or_none()

            recipient_email = settings.recipient_email
            if config:
                recipient_email = config.value

            if not recipient_email:
                logger.warning("No recipient email configured")
                return {
                    "sent": False,
                    "reason": "No recipient email configured"
                }

            # Build URLs using configured base URL
            base_url = settings.app_base_url.rstrip('/')
            download_url = f"{base_url}/api/v1/jobs/{job_id}/download"
            insight_url = f"{base_url}/api/v1/jobs/{job_id}/insight"

            # Count documents
            total_documents = job.total_files - job.failed_files

            # Determine status
            status = job.status.value if not error_message else "failed"

            # Send email
            sent = await email_service.send_job_completion_email(
                job_id=str(job_id),
                job_type=job.type.value,
                recipient_email=recipient_email,
                download_url=download_url,
                insight_url=insight_url,
                total_documents=total_documents,
                status=status,
                error_message=error_message
            )

            logger.info(f"Email notification sent: {sent}")

            return {
                "sent": sent,
                "recipient": recipient_email
            }

        except Exception as e:
            logger.error(f"Email notification failed: {e}")
            # Don't fail the workflow if email fails
            return {
                "sent": False,
                "error": str(e)
            }
