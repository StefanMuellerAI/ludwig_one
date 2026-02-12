"""
Archive Builder Activity - Create output TAR archives
"""
import io
import logging
import tarfile
from datetime import datetime
from typing import Dict, Any
from temporalio import activity
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import async_session_maker
from app.models import Job, Document
from app.models.job import JobStatus

logger = logging.getLogger(__name__)


@activity.defn(name="build_output_archive")
async def build_output_archive(job_id: str) -> Dict[str, Any]:
    """
    Build output TAR archive with categorized documents and insight XML.

    Args:
        job_id: Job UUID

    Returns:
        Dict with archive info
    """
    activity.heartbeat("Building output archive")

    async with async_session_maker() as db:
        try:
            # Get job
            result = await db.execute(
                select(Job).where(Job.id == job_id)
            )
            job = result.scalar_one_or_none()

            if not job:
                raise ValueError(f"Job {job_id} not found")

            # Get documents (excluding merged children) with eager loading
            documents_result = await db.execute(
                select(Document)
                .options(selectinload(Document.category))
                .where(Document.job_id == job_id)
                .where(Document.merged_into_id.is_(None))
            )
            documents = documents_result.scalars().all()

            # Create TAR archive in memory
            tar_buffer = io.BytesIO()

            with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
                # Group documents by category
                by_category = {}
                for doc in documents:
                    category_name = doc.category.name if doc.category else "Sonstiges"
                    if category_name not in by_category:
                        by_category[category_name] = []
                    by_category[category_name].append(doc)

                activity.heartbeat(f"Grouped into {len(by_category)} categories")

                # Add documents to archive
                doc_count = 0
                total_docs = sum(len(docs) for docs in by_category.values())
                for category_name, category_docs in by_category.items():
                    for doc in category_docs:
                        doc_count += 1
                        activity.heartbeat(f"Adding document {doc_count}/{total_docs} to archive")

                        # Determine filename
                        filename = doc.assigned_filename or doc.original_filename

                        # Add extension if missing
                        if not filename.endswith(f".{doc.file_type}"):
                            filename = f"{filename}.{doc.file_type}"

                        # Path in archive
                        archive_path = f"{category_name}/{filename}"

                        # Create TarInfo
                        tarinfo = tarfile.TarInfo(name=archive_path)
                        tarinfo.size = len(doc.original_blob)

                        # Add to archive
                        tar.addfile(tarinfo, io.BytesIO(doc.original_blob))

                        logger.debug(f"Added: {archive_path}")

                # Add insight XML
                if job.insight_xml:
                    xml_bytes = job.insight_xml.encode('utf-8')
                    xml_info = tarfile.TarInfo(name="insight_report.xml")
                    xml_info.size = len(xml_bytes)
                    tar.addfile(xml_info, io.BytesIO(xml_bytes))
                    logger.info("Added insight_report.xml")

            # Get archive bytes
            archive_blob = tar_buffer.getvalue()

            # Update job with archive and mark as completed
            job.output_archive_blob = archive_blob
            job.output_archive_path = f"job_{job.id}_result.tar"
            job.status = JobStatus.COMPLETED
            job.processing_completed_at = datetime.utcnow()

            await db.commit()

            logger.info(f"Built archive: {len(archive_blob)} bytes, {len(documents)} documents")

            return {
                "archive_size": len(archive_blob),
                "documents_count": len(documents),
                "categories_count": len(by_category)
            }

        except Exception as e:
            await db.rollback()
            logger.error(f"Archive building failed: {e}")
            raise
