"""
Categorization Activities - Categorize and rename documents
"""
import logging
from datetime import datetime
from typing import Dict, Any, List
from temporalio import activity
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.models import Job, Document, Extraction, Category, PromptTemplate, APICallLog
from app.services.llm_service import llm_service
from app.schemas.structured import CategorizationResponse, PageCategorizationResponse
from app.config import settings

logger = logging.getLogger(__name__)


@activity.defn(name="categorize_and_rename_document")
async def categorize_and_rename_document(document_id: str) -> Dict[str, Any]:
    """
    Categorize document and assign filename (Flow 1).

    Args:
        document_id: UUID of document to categorize

    Returns:
        Dict with categorization results
    """
    activity.heartbeat("Starting categorization")

    async with async_session_maker() as db:
        try:
            # Get document with extractions
            result = await db.execute(
                select(Document).where(Document.id == document_id)
            )
            document = result.scalar_one_or_none()

            if not document:
                raise ValueError(f"Document {document_id} not found")

            # Get extractions
            extractions_result = await db.execute(
                select(Extraction).where(Extraction.document_id == document_id)
            )
            extractions = extractions_result.scalars().all()

            # Build context from extractions
            context_parts = []
            for extraction in extractions:
                if extraction.content:
                    context_parts.append(extraction.content)

            full_context = "\n\n---\n\n".join(context_parts)

            # Get categories
            categories_result = await db.execute(
                select(Category).where(Category.is_active == True).order_by(Category.display_order)
            )
            categories = categories_result.scalars().all()
            categories_text = "\n".join([f"- {cat.name}: {cat.description}" for cat in categories])

            # Get prompt template
            template_result = await db.execute(
                select(PromptTemplate).where(
                    PromptTemplate.purpose == "categorization_flow1",
                    PromptTemplate.is_active == True
                )
            )
            template = template_result.scalar_one_or_none()

            if not template:
                raise ValueError("Categorization prompt template not found")

            # Truncate context if needed (100k token safe limit)
            token_count = await llm_service.count_tokens(full_context)
            if token_count > 80000:
                logger.warning(f"Context too long ({token_count} tokens), truncating")
                full_context = await llm_service.truncate_to_token_limit(full_context, 80000)

            # Build prompt
            prompt = template.template.format(
                categories=categories_text,
                content=full_context
            )

            activity.heartbeat("Calling LLM for categorization")

            # Call LLM with structured output
            start_time = datetime.utcnow()

            categorization = await llm_service.call_with_structured_output(
                prompt=prompt,
                response_model=CategorizationResponse,
                model_name=template.model_name,
                temperature=template.temperature,
                max_tokens=template.max_tokens
            )

            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            # Find category
            category = next((c for c in categories if c.name == categorization.category), None)

            if not category:
                logger.warning(f"Category '{categorization.category}' not found, using 'Sonstiges'")
                category = next((c for c in categories if c.name == "Sonstiges"), categories[0])

            # Update document
            document.assigned_category_id = category.id
            document.assigned_filename = categorization.new_filename
            document.categorization_confidence = categorization.confidence
            document.processing_status = "categorized"

            # Log API call
            api_log = APICallLog(
                document_id=document.id,
                api_provider="mistral" if not llm_service.use_ollama else "ollama",
                model_name=template.model_name,
                call_type="structured_output",
                prompt_text=prompt[:1000] if settings.log_llm_payloads else None,
                response_text=categorization.model_dump_json() if settings.log_llm_payloads else None,
                duration_ms=duration_ms,
                success=True
            )
            db.add(api_log)

            await db.commit()

            logger.info(f"Categorized as '{category.name}' with filename '{categorization.new_filename}'")

            return {
                "document_id": str(document.id),
                "category": category.name,
                "filename": categorization.new_filename,
                "confidence": categorization.confidence
            }

        except Exception as e:
            await db.rollback()
            logger.error(f"Categorization failed for document {document_id}: {e}")
            raise


@activity.defn(name="categorize_page")
async def categorize_page(document_id: str) -> Dict[str, Any]:
    """
    Categorize a single PDF page (Flow 2 - no filename yet).

    Args:
        document_id: UUID of page document

    Returns:
        Dict with categorization result
    """
    activity.heartbeat("Starting page categorization")

    async with async_session_maker() as db:
        try:
            # Get document
            result = await db.execute(
                select(Document).where(Document.id == document_id)
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

            # Truncate if needed
            token_count = await llm_service.count_tokens(full_context)
            if token_count > 50000:
                full_context = await llm_service.truncate_to_token_limit(full_context, 50000)

            # Get categories
            categories_result = await db.execute(
                select(Category).where(Category.is_active == True).order_by(Category.display_order)
            )
            categories = categories_result.scalars().all()
            categories_text = "\n".join([f"- {cat.name}" for cat in categories])

            # Get prompt template
            template_result = await db.execute(
                select(PromptTemplate).where(
                    PromptTemplate.purpose == "categorization_flow2",
                    PromptTemplate.is_active == True
                )
            )
            template = template_result.scalar_one_or_none()

            if not template:
                raise ValueError("Page categorization template not found")

            # Get categories
            categories_result = await db.execute(
                select(Category).where(Category.is_active == True).order_by(Category.display_order)
            )
            categories = categories_result.scalars().all()
            categories_text = "\n".join([f"- {cat.name}: {cat.description}" for cat in categories])

            # Build prompt
            prompt = template.template.format(
                categories=categories_text,
                content=full_context
            )

            # Call LLM
            start_time = datetime.utcnow()

            categorization = await llm_service.call_with_structured_output(
                prompt=prompt,
                response_model=PageCategorizationResponse,
                model_name=template.model_name,
                temperature=template.temperature,
                max_tokens=template.max_tokens
            )

            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            # Find category
            category = next((c for c in categories if c.name == categorization.category), None)
            if not category:
                category = next((c for c in categories if c.name == "Sonstiges"), categories[0])

            # Update document
            document.assigned_category_id = category.id
            document.categorization_confidence = categorization.confidence
            document.processing_status = "categorized"

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

            logger.info(f"Page categorized as '{category.name}'")

            return {
                "document_id": str(document.id),
                "category": category.name,
                "confidence": categorization.confidence
            }

        except Exception as e:
            await db.rollback()
            logger.error(f"Page categorization failed: {e}")
            raise
