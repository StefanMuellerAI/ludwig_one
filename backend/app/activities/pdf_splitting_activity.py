"""
PDF Splitting Activity - Split PDF into page documents
"""
import logging
from typing import List
from temporalio import activity
from sqlalchemy import select

from app.database import async_session_maker
from app.models import Job, Document
from app.models.job import JobStatus
from app.services.pdf_service import pdf_service

logger = logging.getLogger(__name__)


@activity.defn(name="split_pdf_and_create_pages")
async def split_pdf_and_create_pages(job_id: str) -> List[str]:
    """
    Split PDF into individual pages and create document records.

    Args:
        job_id: Job UUID

    Returns:
        List of page document IDs
    """
    activity.heartbeat("Starting PDF splitting")

    async with async_session_maker() as db:
        try:
            # Get job
            result = await db.execute(
                select(Job).where(Job.id == job_id)
            )
            job = result.scalar_one_or_none()

            if not job:
                raise ValueError(f"Job {job_id} not found")

            # Update job status
            job.status = JobStatus.PROCESSING

            # Get total pages first
            total_pages = await pdf_service.get_page_count(job.original_blob)
            job.total_files = total_pages

            logger.info(f"Splitting PDF into {total_pages} pages")

            # Split PDF and create page documents
            page_ids = []

            async for page_num, page_blob in pdf_service.split_pdf_into_pages(job.original_blob):
                activity.heartbeat(f"Processing page {page_num}/{total_pages}")

                # Create document for each page
                document = Document(
                    job_id=job.id,
                    original_filename=f"{job.original_filename}_page_{page_num}",
                    file_type="pdf",
                    file_size_bytes=len(page_blob),
                    original_blob=page_blob,
                    page_number=page_num,
                    total_pages=1,
                    processing_status="pending"
                )
                db.add(document)
                await db.flush()

                page_ids.append(str(document.id))

                logger.debug(f"Created page document {page_num}/{total_pages}")

            await db.commit()

            logger.info(f"Created {len(page_ids)} page documents")

            return page_ids

        except Exception as e:
            await db.rollback()
            logger.error(f"PDF splitting failed: {e}")
            raise
