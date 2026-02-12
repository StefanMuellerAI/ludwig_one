"""
Job API Endpoints
"""
import logging
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Response, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer
from temporalio.client import Client
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_db
from app.config import settings
from app.models import Job, JobType, JobStatus
from app.schemas.job import JobResponse, JobListResponse, JobCreateResponse
from app.workflows import TarProcessingWorkflow, PdfSplittingWorkflow
from app.auth.dependencies import require_job_access

logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

router = APIRouter()


async def get_temporal_client() -> Client:
    """Get Temporal client dependency"""
    client = await Client.connect(
        settings.temporal_host,
        namespace=settings.temporal_namespace
    )
    return client


@router.post("/tar-upload", response_model=JobCreateResponse)
@limiter.limit("10/hour")
async def upload_tar_archive(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    temporal: Client = Depends(get_temporal_client)
):
    """
    Upload TAR archive for processing (Flow 1).

    Args:
        file: TAR archive file
        db: Database session
        temporal: Temporal client

    Returns:
        Job creation response
    """
    try:
        # Validate file
        if not file.filename.endswith((".tar", ".tar.gz", ".tgz")):
            raise HTTPException(status_code=400, detail="File must be a TAR archive")

        # Read file
        file_blob = await file.read()

        if len(file_blob) > settings.upload_max_size_mb * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size: {settings.upload_max_size_mb}MB"
            )

        # Create job record
        job = Job(
            type=JobType.TAR_PROCESSING,
            status=JobStatus.PENDING,
            original_filename=file.filename,
            original_blob=file_blob
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)

        logger.info(f"Created job {job.id} for TAR processing")

        # Start Temporal workflow
        workflow_id = f"tar-processing-{job.id}"
        handle = await temporal.start_workflow(
            TarProcessingWorkflow.run,
            args=[str(job.id)],
            id=workflow_id,
            task_queue="ludwigone-task-queue"
        )

        # Update job with workflow ID
        job.workflow_id = workflow_id
        await db.commit()

        logger.info(f"Started workflow {workflow_id}")

        return JobCreateResponse(
            job_id=job.id,
            message=f"TAR archive uploaded successfully. Job ID: {job.id}"
        )

    except Exception as e:
        logger.error(f"TAR upload failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/pdf-upload", response_model=JobCreateResponse)
@limiter.limit("10/hour")
async def upload_pdf(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    temporal: Client = Depends(get_temporal_client)
):
    """
    Upload PDF for splitting and processing (Flow 2).

    Args:
        file: PDF file
        db: Database session
        temporal: Temporal client

    Returns:
        Job creation response
    """
    try:
        # Validate file
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="File must be a PDF")

        # Read file
        file_blob = await file.read()

        if len(file_blob) > settings.upload_max_size_mb * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size: {settings.upload_max_size_mb}MB"
            )

        # Create job record
        job = Job(
            type=JobType.PDF_SPLITTING,
            status=JobStatus.PENDING,
            original_filename=file.filename,
            original_blob=file_blob
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)

        logger.info(f"Created job {job.id} for PDF splitting")

        # Start Temporal workflow
        workflow_id = f"pdf-splitting-{job.id}"
        handle = await temporal.start_workflow(
            PdfSplittingWorkflow.run,
            args=[str(job.id)],
            id=workflow_id,
            task_queue="ludwigone-task-queue"
        )

        # Update job with workflow ID
        job.workflow_id = workflow_id
        await db.commit()

        logger.info(f"Started workflow {workflow_id}")

        return JobCreateResponse(
            job_id=job.id,
            message=f"PDF uploaded successfully. Job ID: {job.id}"
        )

    except Exception as e:
        logger.error(f"PDF upload failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("", response_model=JobListResponse)
@limiter.limit("100/minute")
async def list_jobs(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    List all jobs.

    Args:
        skip: Number of jobs to skip
        limit: Maximum number of jobs to return
        db: Database session

    Returns:
        List of jobs
    """
    try:
        # Get total count
        count_result = await db.execute(select(func.count(Job.id)))
        total = count_result.scalar()

        # Get jobs (exclude large BLOB columns)
        result = await db.execute(
            select(Job)
            .options(
                defer(Job.original_blob),
                defer(Job.output_archive_blob),
                defer(Job.insight_xml)
            )
            .order_by(Job.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        jobs = result.scalars().all()

        return JobListResponse(
            jobs=[JobResponse.model_validate(job) for job in jobs],
            total=total
        )

    except Exception as e:
        logger.error(f"Job listing failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{job_id}", response_model=JobResponse)
@limiter.limit("100/minute")
async def get_job_status(
    request: Request,
    job_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get job status and details.

    Args:
        job_id: Job UUID
        db: Database session

    Returns:
        Job details
    """
    try:
        result = await db.execute(
            select(Job)
            .options(
                defer(Job.original_blob),
                defer(Job.output_archive_blob),
                defer(Job.insight_xml)
            )
            .where(Job.id == job_id)
        )
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        return JobResponse.model_validate(job)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Job status retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{job_id}/download", dependencies=[Depends(require_job_access)])
@limiter.limit("20/minute")
async def download_result_archive(
    request: Request,
    job_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Download result archive.

    Args:
        job_id: Job UUID
        db: Database session

    Returns:
        Archive file
    """
    try:
        result = await db.execute(
            select(Job)
            .options(
                defer(Job.original_blob),
                defer(Job.insight_xml)
            )
            .where(Job.id == job_id)
        )
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        if job.status != JobStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Job not completed yet")

        if not job.output_archive_blob:
            raise HTTPException(status_code=404, detail="Output archive not found")

        # Return archive
        return Response(
            content=job.output_archive_blob,
            media_type="application/gzip",
            headers={
                "Content-Disposition": f"attachment; filename={job.output_archive_path}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Archive download failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{job_id}/insight", dependencies=[Depends(require_job_access)])
@limiter.limit("20/minute")
async def get_insight_report(
    request: Request,
    job_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get insight XML report.

    Args:
        job_id: Job UUID
        db: Database session

    Returns:
        XML content
    """
    try:
        result = await db.execute(
            select(Job)
            .options(
                defer(Job.original_blob),
                defer(Job.output_archive_blob)
            )
            .where(Job.id == job_id)
        )
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        if job.status != JobStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Job not completed yet")

        if not job.insight_xml:
            raise HTTPException(status_code=404, detail="Insight report not found")

        # Return XML
        return Response(
            content=job.insight_xml,
            media_type="application/xml",
            headers={
                "Content-Disposition": f"attachment; filename=insight_{job.id}.xml"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Insight retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{job_id}")
@limiter.limit("10/minute")
async def delete_job(
    request: Request,
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    temporal: Client = Depends(get_temporal_client)
):
    """
    Delete job and all associated data.
    If job is running, it will be cancelled first.

    Args:
        job_id: Job UUID
        db: Database session
        temporal: Temporal client

    Returns:
        Success message
    """
    try:
        result = await db.execute(
            select(Job)
            .options(
                defer(Job.original_blob),
                defer(Job.output_archive_blob),
                defer(Job.insight_xml)
            )
            .where(Job.id == job_id)
        )
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Cancel workflow if running
        if job.status in [JobStatus.PENDING, JobStatus.PROCESSING]:
            if job.workflow_id:
                try:
                    handle = temporal.get_workflow_handle(job.workflow_id)
                    await handle.cancel()
                    logger.info(f"Cancelled workflow {job.workflow_id}")
                except Exception as e:
                    logger.warning(f"Failed to cancel workflow: {e}")

        # Delete job (CASCADE will delete documents, extractions, etc.)
        await db.delete(job)
        await db.commit()

        logger.info(f"Deleted job {job_id}")

        return {"message": "Job deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Job deletion failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
