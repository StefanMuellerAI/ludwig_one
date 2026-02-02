"""
Temporal Worker - Executes workflows and activities
"""
import asyncio
import logging
from temporalio.client import Client
from temporalio.worker import Worker

from app.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    """Main worker function"""
    logger.info("Starting Temporal Worker...")

    # Connect to Temporal server
    client = await Client.connect(
        settings.temporal_host,
        namespace=settings.temporal_namespace
    )
    logger.info(f"Connected to Temporal at {settings.temporal_host}")

    # Import workflows and activities
    from app.workflows import TarProcessingWorkflow, PdfSplittingWorkflow
    from app.activities import (
        extract_tar_and_create_documents,
        split_pdf_and_create_pages,
        extract_document_content,
        categorize_and_rename_document,
        categorize_page,
        get_pages_by_category,
        should_merge_documents,
        merge_documents,
        assign_filename_to_merged_document,
        generate_insight_report,
        build_output_archive,
        send_job_completion_email,
        update_job_status_to_failed
    )

    # Create worker
    worker = Worker(
        client,
        task_queue="ludwigone-task-queue",
        workflows=[TarProcessingWorkflow, PdfSplittingWorkflow],
        activities=[
            extract_tar_and_create_documents,
            split_pdf_and_create_pages,
            extract_document_content,
            categorize_and_rename_document,
            categorize_page,
            get_pages_by_category,
            should_merge_documents,
            merge_documents,
            assign_filename_to_merged_document,
            generate_insight_report,
            build_output_archive,
            send_job_completion_email,
            update_job_status_to_failed
        ],
        max_concurrent_activities=settings.max_concurrent_vision_calls,
    )

    logger.info("Worker registered with task queue: ludwigone-task-queue")
    logger.info(f"Max concurrent activities: {settings.max_concurrent_vision_calls}")

    # Run worker
    try:
        logger.info("Worker is running and waiting for tasks...")
        await worker.run()
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user")
    except Exception as e:
        logger.error(f"Worker error: {e}", exc_info=True)
        raise
    finally:
        logger.info("Worker shutting down")


if __name__ == "__main__":
    asyncio.run(main())
