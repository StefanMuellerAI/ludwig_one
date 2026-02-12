"""
Archive Extraction Activity - Supports TAR and ZIP
"""
import logging
import io
import os
import tarfile
import zipfile
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
    Extract TAR or ZIP archive and create document records.

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

        # Detect archive type and extract
        filename = (job.original_filename or "").lower()
        is_zip = filename.endswith('.zip')

        if is_zip:
            logger.info(f"Starting ZIP extraction for job {job_id}")
            document_ids = await _extract_zip(db, job)
        else:
            logger.info(f"Starting TAR extraction for job {job_id}")
            document_ids = await _extract_tar(db, job)

        return document_ids


async def _extract_tar(db, job) -> List[str]:
    """Extract files from TAR archive"""
    tar_buffer = io.BytesIO(job.original_blob)
    document_ids = []

    try:
        with tarfile.open(fileobj=tar_buffer, mode='r:*') as tar:
            members = tar.getmembers()
            skipped_files = 0

            logger.info(f"Found {len([m for m in members if m.isfile()])} total files in TAR archive")

            for file_idx, member in enumerate(members):
                if not member.isfile():
                    continue

                activity.heartbeat(f"Extracting file {file_idx + 1}")

                # Security: Prevent path traversal attacks
                if member.name.startswith('/') or member.name.startswith('..') or '..' in member.name:
                    logger.warning(f"Skipping potentially malicious path: {member.name}")
                    skipped_files += 1
                    continue

                # Security: Block symlinks and hardlinks
                if member.issym() or member.islnk():
                    logger.warning(f"Skipping symlink/hardlink: {member.name}")
                    skipped_files += 1
                    continue

                # Sanitize filename, skip macOS metadata files (._*) and hidden files
                safe_filename = os.path.basename(member.name)
                if not safe_filename or safe_filename.startswith('.'):
                    logger.debug(f"Skipping hidden/metadata file: {member.name}")
                    skipped_files += 1
                    continue

                # Extract file
                file_obj = tar.extractfile(member)
                if file_obj:
                    file_content = file_obj.read()

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

            # Set total_files to actual processable documents (not metadata)
            job.total_files = len(document_ids)
            await db.commit()

            if skipped_files > 0:
                logger.info(f"Skipped {skipped_files} hidden/metadata files")
            logger.info(f"Created {len(document_ids)} document records from TAR")

    except Exception as e:
        logger.error(f"TAR extraction failed: {e}")
        job.status = JobStatus.FAILED
        job.error_message = str(e)
        await db.commit()
        raise

    return document_ids


async def _extract_zip(db, job) -> List[str]:
    """Extract files from ZIP archive"""
    zip_buffer = io.BytesIO(job.original_blob)
    document_ids = []

    try:
        with zipfile.ZipFile(zip_buffer, 'r') as zf:
            members = [m for m in zf.infolist() if not m.is_dir()]
            skipped_files = 0

            logger.info(f"Found {len(members)} total files in ZIP archive")

            for file_idx, member in enumerate(members):
                activity.heartbeat(f"Extracting file {file_idx + 1}")

                # Security: Prevent path traversal attacks
                if member.filename.startswith('/') or '..' in member.filename:
                    logger.warning(f"Skipping potentially malicious path: {member.filename}")
                    skipped_files += 1
                    continue

                # Sanitize filename, skip macOS metadata files and hidden files
                safe_filename = os.path.basename(member.filename)
                if not safe_filename or safe_filename.startswith('.'):
                    logger.debug(f"Skipping hidden/metadata file: {member.filename}")
                    skipped_files += 1
                    continue

                # Skip __MACOSX directory entries
                if '__MACOSX' in member.filename:
                    logger.debug(f"Skipping macOS metadata: {member.filename}")
                    skipped_files += 1
                    continue

                # Extract file
                file_content = zf.read(member.filename)

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

            # Set total_files to actual processable documents (not metadata)
            job.total_files = len(document_ids)
            await db.commit()

            if skipped_files > 0:
                logger.info(f"Skipped {skipped_files} hidden/metadata files")
            logger.info(f"Created {len(document_ids)} document records from ZIP")

    except Exception as e:
        logger.error(f"ZIP extraction failed: {e}")
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
