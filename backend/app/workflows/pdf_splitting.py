"""
PDF Splitting Workflow - Flow 2
Split → Process → Categorize → Merge → Rename → Build Archive → Insight
"""
import asyncio
import logging
from datetime import timedelta
from typing import List, Dict, Any
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from app.activities import (
        split_pdf_and_create_pages,
        extract_document_content,
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

logger = logging.getLogger(__name__)


@workflow.defn(name="PdfSplittingWorkflow")
class PdfSplittingWorkflow:
    """Workflow for splitting and intelligently merging PDFs (Flow 2)"""

    @workflow.run
    async def run(self, job_id: str) -> Dict[str, Any]:
        """
        Execute PDF splitting workflow.

        Args:
            job_id: Job UUID

        Returns:
            Dict with workflow results
        """
        workflow.logger.info(f"Starting PDF splitting workflow for job {job_id}")

        try:
            # Step 1: Split PDF into pages
            workflow.logger.info("Step 1: Splitting PDF into pages")
            page_ids = await workflow.execute_activity(
                split_pdf_and_create_pages,
                args=[job_id],
                start_to_close_timeout=timedelta(minutes=30),
                retry_policy=RetryPolicy(maximum_attempts=3)
            )
            workflow.logger.info(f"Split into {len(page_ids)} pages")

            # Step 2: Process pages in parallel (max 5 concurrent)
            workflow.logger.info("Step 2: Processing pages")
            processed_ids = []

            for i in range(0, len(page_ids), 5):
                batch = page_ids[i:i + 5]

                extraction_tasks = []
                for page_id in batch:
                    task = workflow.execute_activity(
                        extract_document_content,
                        args=[page_id],
                        start_to_close_timeout=timedelta(minutes=30),
                        heartbeat_timeout=timedelta(minutes=10),
                        retry_policy=RetryPolicy(
                            maximum_attempts=3,
                            initial_interval=timedelta(seconds=5),
                            backoff_coefficient=1.5,
                            maximum_interval=timedelta(seconds=30)
                        )
                    )
                    extraction_tasks.append(task)

                batch_results = await asyncio.gather(*extraction_tasks)
                processed_ids.extend([r["document_id"] for r in batch_results])

                workflow.logger.info(f"Processed page batch {i // 5 + 1}")

            # Step 3: Categorize pages (sequential for ordering)
            workflow.logger.info("Step 3: Categorizing pages")

            for page_id in processed_ids:
                await workflow.execute_activity(
                    categorize_page,
                    args=[page_id],
                    start_to_close_timeout=timedelta(minutes=10),
                    retry_policy=RetryPolicy(maximum_attempts=3)
                )

            workflow.logger.info(f"Categorized {len(processed_ids)} pages")

            # Step 4: Intelligent merging by category
            workflow.logger.info("Step 4: Merging related pages")
            merged_ids = await self._merge_pages_by_category(job_id, processed_ids)
            workflow.logger.info(f"Merged into {len(merged_ids)} documents")

            # Step 5: Assign filenames to merged documents in parallel
            workflow.logger.info("Step 5: Assigning filenames")

            filename_tasks = []
            for doc_id in merged_ids:
                task = workflow.execute_activity(
                    assign_filename_to_merged_document,
                    args=[doc_id],
                    start_to_close_timeout=timedelta(minutes=10),
                    retry_policy=RetryPolicy(maximum_attempts=3)
                )
                filename_tasks.append(task)

            await asyncio.gather(*filename_tasks)

            # Step 6: Generate insight report
            workflow.logger.info("Step 6: Generating insight report")
            await workflow.execute_activity(
                generate_insight_report,
                args=[job_id],
                start_to_close_timeout=timedelta(minutes=15),
                retry_policy=RetryPolicy(maximum_attempts=3)
            )

            # Step 7: Build output archive
            workflow.logger.info("Step 7: Building output archive")
            archive_info = await workflow.execute_activity(
                build_output_archive,
                args=[job_id],
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=RetryPolicy(maximum_attempts=3)
            )

            # Step 8: Send email notification
            workflow.logger.info("Step 8: Sending notification")
            await workflow.execute_activity(
                send_job_completion_email,
                args=[job_id],
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=RetryPolicy(maximum_attempts=2)
            )

            workflow.logger.info("PDF splitting workflow completed successfully")

            return {
                "job_id": job_id,
                "pages_processed": len(processed_ids),
                "documents_created": len(merged_ids),
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

    async def _merge_pages_by_category(self, job_id: str, page_ids: List[str]) -> List[str]:
        """
        Intelligently merge pages by category using LLM decisions.

        Args:
            job_id: Job UUID
            page_ids: List of page document IDs

        Returns:
            List of merged document IDs
        """
        # Get pages grouped by category
        by_category = await workflow.execute_activity(
            get_pages_by_category,
            args=[job_id, page_ids],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )

        workflow.logger.info(f"Grouped into {len(by_category)} categories")

        merged_doc_ids = []

        # Process each category
        for category_name, category_page_ids in by_category.items():
            workflow.logger.info(f"Merging category: {category_name} ({len(category_page_ids)} pages)")

            if len(category_page_ids) == 1:
                # Single page, no merging needed
                merged_doc_ids.append(category_page_ids[0])
                continue

            # Sequential merging with LLM decisions
            current_doc_id = category_page_ids[0]

            for next_page_id in category_page_ids[1:]:
                # Ask LLM if should merge
                should_merge = await workflow.execute_activity(
                    should_merge_documents,
                    args=[current_doc_id, next_page_id],
                    start_to_close_timeout=timedelta(minutes=10),
                    retry_policy=RetryPolicy(maximum_attempts=3)
                )

                if should_merge:
                    # Merge documents
                    merged_id = await workflow.execute_activity(
                        merge_documents,
                        args=[current_doc_id, next_page_id],
                        start_to_close_timeout=timedelta(minutes=5),
                        retry_policy=RetryPolicy(maximum_attempts=3)
                    )
                    # Update current doc reference
                    current_doc_id = merged_id

                    workflow.logger.debug(f"Merged page into document")
                else:
                    # Start new document
                    merged_doc_ids.append(current_doc_id)
                    current_doc_id = next_page_id

            # Add last document
            merged_doc_ids.append(current_doc_id)

        workflow.logger.info(f"Created {len(merged_doc_ids)} merged documents")

        return merged_doc_ids
