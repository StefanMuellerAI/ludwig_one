"""
Merging Activities - Intelligent PDF page merging for Flow 2
"""
import logging
from datetime import datetime
from typing import Dict, Any, List
from temporalio import activity
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import async_session_maker
from app.models import Document, Extraction, PromptTemplate, APICallLog
from app.services.llm_service import llm_service
from app.services.pdf_service import pdf_service
from app.schemas.structured import MergeDecision, FilenameGenerationResponse

logger = logging.getLogger(__name__)


@activity.defn(name="should_merge_documents")
async def should_merge_documents(doc1_id: str, doc2_id: str) -> bool:
    """
    Determine if two documents should be merged together.

    Args:
        doc1_id: First document UUID
        doc2_id: Second document UUID

    Returns:
        True if documents should be merged
    """
    activity.heartbeat("Checking merge decision")

    async with async_session_maker() as db:
        try:
            # Get both documents
            result = await db.execute(
                select(Document).where(Document.id.in_([doc1_id, doc2_id]))
            )
            documents = result.scalars().all()

            if len(documents) != 2:
                raise ValueError("Both documents must exist")

            doc1, doc2 = documents[0], documents[1]

            # Get extractions for both documents (contains vision API analysis)
            extractions_result = await db.execute(
                select(Extraction).where(
                    Extraction.document_id.in_([doc1_id, doc2_id])
                ).order_by(Extraction.created_at)
            )
            all_extractions = extractions_result.scalars().all()

            # Build content from extractions for each document
            doc1_extractions = [e for e in all_extractions if e.document_id == doc1.id]
            doc2_extractions = [e for e in all_extractions if e.document_id == doc2.id]

            doc1_parts = [e.content for e in doc1_extractions if e.content]
            doc2_parts = [e.content for e in doc2_extractions if e.content]

            doc1_text = "\n\n".join(doc1_parts) if doc1_parts else "No content available"
            doc2_text = "\n\n".join(doc2_parts) if doc2_parts else "No content available"

            # Truncate for token limit
            doc1_text = await llm_service.truncate_to_token_limit(doc1_text, 30000)
            doc2_text = await llm_service.truncate_to_token_limit(doc2_text, 30000)

            # Get prompt template
            template_result = await db.execute(
                select(PromptTemplate).where(
                    PromptTemplate.purpose == "merge_decision_flow2",
                    PromptTemplate.is_active == True
                )
            )
            template = template_result.scalar_one_or_none()

            if not template:
                raise ValueError("Merge decision template not found")

            # Build prompt
            prompt = template.template.format(
                doc1_content=doc1_text,
                doc2_content=doc2_text
            )

            # Call LLM
            start_time = datetime.utcnow()

            decision = await llm_service.call_with_structured_output(
                prompt=prompt,
                response_model=MergeDecision,
                model_name=template.model_name,
                temperature=template.temperature,
                max_tokens=template.max_tokens
            )

            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            # Log API call
            api_log = APICallLog(
                document_id=doc1.id,
                api_provider="mistral" if not llm_service.use_ollama else "ollama",
                model_name=template.model_name,
                call_type="structured_output",
                duration_ms=duration_ms,
                success=True
            )
            db.add(api_log)
            await db.commit()

            logger.info(f"Merge decision for {doc1.page_number}/{doc2.page_number}: {decision.should_merge} - {decision.reasoning}")

            return decision.should_merge

        except Exception as e:
            await db.rollback()
            logger.error(f"Merge decision failed: {e}")
            raise


@activity.defn(name="merge_documents")
async def merge_documents(doc1_id: str, doc2_id: str) -> str:
    """
    Merge two documents together.

    Args:
        doc1_id: Parent document UUID
        doc2_id: Document to merge into parent

    Returns:
        Parent document ID
    """
    activity.heartbeat("Merging documents")

    async with async_session_maker() as db:
        try:
            # Get both documents
            result = await db.execute(
                select(Document).where(Document.id.in_([doc1_id, doc2_id]))
            )
            documents = result.scalars().all()

            if len(documents) != 2:
                raise ValueError("Both documents must exist")

            doc1, doc2 = documents[0], documents[1]

            # Merge PDFs
            merged_blob = await pdf_service.merge_pdfs([doc1.original_blob, doc2.original_blob])

            # Update parent document
            doc1.original_blob = merged_blob
            doc1.is_merged_parent = True
            doc1.total_pages = await pdf_service.get_page_count(merged_blob)

            # Update child document
            doc2.merged_into_id = doc1.id

            await db.commit()

            logger.info(f"Merged doc {doc2.page_number} into doc {doc1.page_number}")

            return str(doc1.id)

        except Exception as e:
            await db.rollback()
            logger.error(f"Document merge failed: {e}")
            raise


@activity.defn(name="assign_filename_to_merged_document")
async def assign_filename_to_merged_document(document_id: str) -> str:
    """
    Assign filename to merged document (Flow 2).

    Args:
        document_id: Document UUID

    Returns:
        Assigned filename
    """
    activity.heartbeat("Assigning filename")

    async with async_session_maker() as db:
        try:
            # Get document with eager loading
            result = await db.execute(
                select(Document)
                .options(selectinload(Document.category))
                .where(Document.id == document_id)
            )
            document = result.scalar_one_or_none()

            if not document:
                raise ValueError(f"Document {document_id} not found")

            # Get extractions
            extractions_result = await db.execute(
                select(Extraction).where(Extraction.document_id == document_id)
            )
            extractions = extractions_result.scalars().all()

            # Build context
            context_parts = [e.content for e in extractions if e.content]
            full_context = "\n\n".join(context_parts)

            # Truncate
            full_context = await llm_service.truncate_to_token_limit(full_context, 50000)

            # Get category name
            category_name = document.category.name if document.category else "Unknown"

            # Get prompt template
            template_result = await db.execute(
                select(PromptTemplate).where(
                    PromptTemplate.purpose == "filename_generation_flow2",
                    PromptTemplate.is_active == True
                )
            )
            template = template_result.scalar_one_or_none()

            if not template:
                raise ValueError("Filename generation template not found")

            # Build prompt
            prompt = template.template.format(
                content=full_context,
                category=category_name
            )

            # Call LLM
            start_time = datetime.utcnow()

            filename_response = await llm_service.call_with_structured_output(
                prompt=prompt,
                response_model=FilenameGenerationResponse,
                model_name=template.model_name,
                temperature=template.temperature,
                max_tokens=template.max_tokens
            )

            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            # Update document
            document.assigned_filename = filename_response.new_filename
            document.processing_status = "completed"

            # Log API call
            api_log = APICallLog(
                document_id=document.id,
                api_provider="mistral" if not llm_service.use_ollama else "ollama",
                model_name=template.model_name,
                call_type="structured_output",
                duration_ms=duration_ms,
                success=True
            )
            db.add(api_log)

            await db.commit()

            logger.info(f"Assigned filename: {filename_response.new_filename}")

            return filename_response.new_filename

        except Exception as e:
            await db.rollback()
            logger.error(f"Filename assignment failed: {e}")
            raise
