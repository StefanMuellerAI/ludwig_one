"""
TAR Processing Workflow - Flow 1
Extract → Process → Categorize → Rename → Build Archive → Insight
"""
import asyncio
import logging
import tarfile
import io
from datetime import timedelta
from typing import List, Dict, Any
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from app.activities import (
        extract_tar_and_create_documents,
        extract_document_content,
        categorize_and_rename_document,
        generate_insight_report,
        build_output_archive,
        send_job_completion_email,
        update_job_status_to_failed
    )

logger = logging.getLogger(__name__)


@workflow.defn(name="TarProcessingWorkflow")
class TarProcessingWorkflow:
    """Workflow for processing TAR archives (Flow 1)"""

    @workflow.run
    async def run(self, job_id: str) -> Dict[str, Any]:
        """
        Execute TAR processing workflow.

        Args:
            job_id: Job UUID

        Returns:
            Dict with workflow results
        """
        workflow.logger.info(f"Starting TAR processing workflow for job {job_id}")

        try:
            # Step 1: Extract TAR archive and create document records
            workflow.logger.info("Step 1: Extracting TAR archive")
            document_ids = await workflow.execute_activity(
                extract_tar_and_create_documents,
                args=[job_id],
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=RetryPolicy(maximum_attempts=3)
            )
            workflow.logger.info(f"Extracted and created {len(document_ids)} documents")

            # Step 2: Extract content from documents (text/images) in parallel (max 5 concurrent)
            workflow.logger.info("Step 2: Extracting content from documents")

            # Process in batches of 5
            for i in range(0, len(document_ids), 5):
                batch = document_ids[i:i + 5]

                extraction_tasks = []
                for doc_id in batch:
                    task = workflow.execute_activity(
                        extract_document_content,
                        args=[doc_id],
                        start_to_close_timeout=timedelta(minutes=10),
                        heartbeat_timeout=timedelta(minutes=5),
                        retry_policy=RetryPolicy(
                            maximum_attempts=3,
                            initial_interval=timedelta(seconds=5),
                            backoff_coefficient=1.5,
                            maximum_interval=timedelta(seconds=30)
                        )
                    )
                    extraction_tasks.append(task)

                # Wait for batch to complete
                batch_results = await asyncio.gather(*extraction_tasks)

                workflow.logger.info(f"Processed batch {i // 5 + 1}, total: {len(batch_results)} extractions")

            # Step 3: Categorize and rename documents in parallel
            workflow.logger.info("Step 3: Categorizing documents")

            categorization_tasks = []
            for doc_id in document_ids:
                task = workflow.execute_activity(
                    categorize_and_rename_document,
                    args=[doc_id],
                    start_to_close_timeout=timedelta(minutes=10),
                    retry_policy=RetryPolicy(
                        maximum_attempts=3,
                        initial_interval=timedelta(seconds=5),
                        backoff_coefficient=2.0
                    )
                )
                categorization_tasks.append(task)

            categorization_results = await asyncio.gather(*categorization_tasks)
            workflow.logger.info(f"Categorized {len(categorization_results)} documents")

            # Step 4: Generate insight report
            workflow.logger.info("Step 4: Generating insight report")
            insight_xml = await workflow.execute_activity(
                generate_insight_report,
                args=[job_id],
                start_to_close_timeout=timedelta(minutes=15),
                retry_policy=RetryPolicy(maximum_attempts=3)
            )

            # Step 5: Build output archive
            workflow.logger.info("Step 5: Building output archive")
            archive_info = await workflow.execute_activity(
                build_output_archive,
                args=[job_id],
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=RetryPolicy(maximum_attempts=3)
            )

            # Step 6: Send email notification
            workflow.logger.info("Step 6: Sending notification")
            await workflow.execute_activity(
                send_job_completion_email,
                args=[job_id],
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=RetryPolicy(maximum_attempts=2)
            )

            workflow.logger.info("TAR processing workflow completed successfully")

            return {
                "job_id": job_id,
                "files_processed": len(document_ids),
                "archive_size": archive_info["archive_size"],
                "status": "completed"
            }

        except Exception as e:
            workflow.logger.error(f"Workflow failed: {e}")

            # Update job status to failed
            try:
                await workflow.execute_activity(
                    update_job_status_to_failed,
                    args=[job_id, str(e)],
                    start_to_close_timeout=timedelta(seconds=30),
                    retry_policy=RetryPolicy(maximum_attempts=3)
                )
            except Exception as update_error:
                workflow.logger.error(f"Failed to update job status: {update_error}")

            # Send failure notification email
            try:
                await workflow.execute_activity(
                    send_job_completion_email,
                    args=[job_id, str(e)],
                    start_to_close_timeout=timedelta(minutes=2),
                    retry_policy=RetryPolicy(maximum_attempts=2)
                )
            except Exception as email_error:
                workflow.logger.error(f"Failed to send failure email: {email_error}")

            raise

    async def _extract_tar_archive(self, job_id: str) -> List[str]:
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
            job.processing_started_at = workflow.now()

            # Extract TAR
            tar_buffer = io.BytesIO(job.original_blob)
            document_ids = []

            with tarfile.open(fileobj=tar_buffer, mode="r:*") as tar:
                members = [m for m in tar.getmembers() if m.isfile()]
                job.total_files = len(members)

                for member in members:
                    workflow.logger.debug(f"Extracting: {member.name}")

                    # Read file content
                    file_obj = tar.extractfile(member)
                    if file_obj:
                        file_blob = file_obj.read()

                        # Detect file type
                        file_type = await document_processor.detect_file_type(
                            file_blob,
                            member.name
                        )

                        # Create document record
                        document = Document(
                            job_id=job.id,
                            original_filename=member.name,
                            file_type=file_type,
                            file_size_bytes=len(file_blob),
                            original_blob=file_blob,
                            processing_status="pending"
                        )
                        db.add(document)
                        await db.flush()

                        document_ids.append(str(document.id))

            await db.commit()

            workflow.logger.info(f"Extracted {len(document_ids)} files from TAR")

            return document_ids
