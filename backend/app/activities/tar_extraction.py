"""
TAR Extraction Activity
"""
import logging
import io
import tarfile
from typing import List, Dict, Any
from temporalio import activity
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.models import Job, Document, JobStatus

logger = logging.getLogger(__name__)


@activity.defn
async def extract_tar_and_create_documents(job_id: str) -> List[str]:
    """
    Extract TAR archive and create document records.

    Args:
        job_id: Job UUID

    Returns:
        List of document IDs
    """
    async with async_session_maker() as db:
        # Get job
        result = await db.execute(
            select(Job).where(Job.id == job_id)
        )
        job = result.scalar_one_or_none()

        if not job:
            raise ValueError(f"Job {job_id} not found")

        # Update job status
        job.status = JobStatus.PROCESSING
        await db.commit()

        logger.info(f"Starting TAR extraction for job {job_id}")

        # Extract TAR
        tar_buffer = io.BytesIO(job.original_blob)
        document_ids = []

        try:
            with tarfile.open(fileobj=tar_buffer, mode='r:*') as tar:
                members = tar.getmembers()
                total_files = len([m for m in members if m.isfile()])
                job.total_files = total_files
                await db.commit()

                logger.info(f"Found {total_files} files in TAR archive")

                for member in members:
                    if not member.isfile():
                        continue

                    # Security: Prevent path traversal attacks
                    if member.name.startswith('/') or member.name.startswith('..') or '..' in member.name:
                        logger.warning(f"Skipping potentially malicious path: {member.name}")
                        continue

                    # Security: Block symlinks and hardlinks
                    if member.issym() or member.islnk():
                        logger.warning(f"Skipping symlink/hardlink: {member.name}")
                        continue

                    # Security: Sanitize filename
                    import os
                    safe_filename = os.path.basename(member.name)
                    if not safe_filename or safe_filename.startswith('.'):
                        logger.warning(f"Skipping invalid filename: {member.name}")
                        continue

                    # Extract file
                    file_obj = tar.extractfile(member)
                    if file_obj:
                        file_content = file_obj.read()

                        # Create document record
                        doc = Document(
                            job_id=job.id,
                            original_filename=safe_filename,
                            file_type=_get_file_type(safe_filename),
                            original_blob=file_content
                        )
                        db.add(doc)
                        await db.flush()
                        document_ids.append(str(doc.id))

                        logger.debug(f"Created document {doc.id} for file {safe_filename}")

                await db.commit()
                logger.info(f"Created {len(document_ids)} document records")

        except Exception as e:
            logger.error(f"TAR extraction failed: {e}")
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            await db.commit()
            raise

        return document_ids


def _get_file_type(filename: str) -> str:
    """Get file type from filename extension"""
    ext = filename.lower().split('.')[-1] if '.' in filename else ''

    type_mapping = {
        'pdf': 'pdf',
        'docx': 'docx',
        'doc': 'doc',
        'xlsx': 'xlsx',
        'xls': 'xls',
        'png': 'image',
        'jpg': 'image',
        'jpeg': 'image',
        'gif': 'image',
        'bmp': 'image',
        'tiff': 'image',
        'txt': 'text',
        'csv': 'text',
    }

    return type_mapping.get(ext, 'unknown')
