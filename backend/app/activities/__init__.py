"""
Temporal Activities
"""
from app.activities.tar_extraction import extract_tar_and_create_documents
from app.activities.pdf_splitting_activity import split_pdf_and_create_pages
from app.activities.extraction import extract_document_content
from app.activities.categorization import (
    categorize_and_rename_document,
    categorize_page
)
from app.activities.merging import (
    should_merge_documents,
    merge_documents,
    assign_filename_to_merged_document
)
from app.activities.intelligent_merging import get_pages_by_category
from app.activities.insight_generation import generate_insight_report
from app.activities.archive_builder import build_output_archive
from app.activities.email_notification import send_job_completion_email
from app.activities.job_status import update_job_status_to_failed

__all__ = [
    "extract_tar_and_create_documents",
    "split_pdf_and_create_pages",
    "extract_document_content",
    "categorize_and_rename_document",
    "categorize_page",
    "should_merge_documents",
    "merge_documents",
    "assign_filename_to_merged_document",
    "get_pages_by_category",
    "generate_insight_report",
    "build_output_archive",
    "send_job_completion_email",
    "update_job_status_to_failed",
]
