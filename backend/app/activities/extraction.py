"""
Extraction Activities - Extract content from documents
"""
import logging
from datetime import datetime
from typing import Dict, Any
from temporalio import activity
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.models import Job, Document, Extraction, ExtractionType, APICallLog
from app.services.document_processor import document_processor
from app.services.llm_service import llm_service
from app.config import settings

logger = logging.getLogger(__name__)


@activity.defn(name="extract_document_content")
async def extract_document_content(document_id: str) -> Dict[str, Any]:
    """
    Extract text and images from a document.

    Args:
        document_id: UUID of document to process

    Returns:
        Dict with extraction results
    """
    activity.heartbeat("Starting extraction")

    async with async_session_maker() as db:
        try:
            # Get document
            result = await db.execute(
                select(Document).where(Document.id == document_id)
            )
            document = result.scalar_one_or_none()

            if not document:
                raise ValueError(f"Document {document_id} not found")

            logger.info(f"Extracting content from {document.original_filename}")

            # Extract content based on file type -- catch errors to continue processing
            text_content = None
            images = []
            content_extraction_error = None
            try:
                text_content, images = await document_processor.extract_content(
                    document.original_blob,
                    document.file_type
                )
            except Exception as e:
                content_extraction_error = str(e)
                logger.error(f"Content extraction failed for {document.original_filename}: {e}, continuing with empty content")

            activity.heartbeat(f"Extracted {len(images)} images")

            # Store text extraction
            text_extraction = None
            if text_content:
                token_count = await llm_service.count_tokens(text_content)
                text_extraction = Extraction(
                    document_id=document.id,
                    extraction_type=ExtractionType.TEXT,
                    content=text_content,
                    token_count=token_count,
                    extraction_status="completed"
                )
                db.add(text_extraction)
                logger.info(f"Text extraction: {token_count} tokens")

            # Process images with Vision API
            vision_extractions = []
            vision_failures = 0
            for idx, image_blob in enumerate(images):
                activity.heartbeat(f"Processing image {idx + 1}/{len(images)}")

                try:
                    # Optimize image
                    optimized_image = await document_processor.optimize_image_for_vision_api(image_blob)

                    # Call Vision API (LLM service handles retries internally)
                    start_time = datetime.utcnow()

                    vision_text = await llm_service.call_vision_api(
                        optimized_image,
                        "Describe this image in detail. Extract all visible text."
                    )

                    activity.heartbeat(f"Vision API completed for image {idx + 1}")

                    duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

                    # Store extraction
                    token_count = await llm_service.count_tokens(vision_text)
                    vision_extraction = Extraction(
                        document_id=document.id,
                        extraction_type=ExtractionType.VISION,
                        content=vision_text,
                        image_blob=optimized_image,
                        token_count=token_count,
                        model_used="mistral-large-latest",
                        processing_time_ms=duration_ms,
                        extraction_status="completed"
                    )
                    db.add(vision_extraction)
                    vision_extractions.append(vision_extraction)

                    # Log API call
                    api_log = APICallLog(
                        document_id=document.id,
                        extraction_id=vision_extraction.id,
                        api_provider="mistral" if not llm_service.use_ollama else "ollama",
                        model_name="mistral-large-latest",
                        call_type="vision",
                        image_count=1,
                        response_text=vision_text[:1000] if settings.log_llm_payloads else None,
                        total_tokens=token_count,
                        duration_ms=duration_ms,
                        success=True
                    )
                    db.add(api_log)

                    logger.info(f"Vision extraction {idx + 1}: {token_count} tokens in {duration_ms}ms")

                except Exception as e:
                    vision_failures += 1
                    logger.error(f"Vision API failed for image {idx + 1}/{len(images)}: {e}")

                    # Store failed extraction but continue with remaining images
                    failed_extraction = Extraction(
                        document_id=document.id,
                        extraction_type=ExtractionType.VISION,
                        image_blob=image_blob,
                        extraction_status="failed",
                        error_message=str(e)[:500]
                    )
                    db.add(failed_extraction)

                    # Log failed API call
                    api_log = APICallLog(
                        document_id=document.id,
                        api_provider="mistral" if not llm_service.use_ollama else "ollama",
                        model_name="mistral-large-latest",
                        call_type="vision",
                        image_count=1,
                        success=False,
                        error_message=str(e)[:500]
                    )
                    db.add(api_log)

            if vision_failures > 0:
                logger.warning(f"Document {document.original_filename}: {vision_failures}/{len(images)} vision extractions failed")

            # Update document status -- mark as extracted even with partial failures
            extraction_status = "extracted"
            if content_extraction_error and not text_content and not vision_extractions:
                extraction_status = "extraction_failed"
            elif vision_failures > 0:
                extraction_status = "extracted_partial"

            document.processing_status = extraction_status
            document.total_tokens = sum([
                text_extraction.token_count if text_extraction else 0,
                *[ve.token_count for ve in vision_extractions]
            ])

            await db.commit()

            # Atomically increment job progress counter for live tracking
            await db.execute(
                update(Job)
                .where(Job.id == document.job_id)
                .values(processed_files=Job.processed_files + 1)
            )
            await db.commit()

            return {
                "document_id": str(document.id),
                "text_extracted": text_content is not None,
                "images_processed": len(images),
                "images_successful": len(vision_extractions),
                "images_failed": vision_failures,
                "total_tokens": document.total_tokens,
                "status": extraction_status
            }

        except Exception as e:
            await db.rollback()
            logger.error(f"Extraction failed for document {document_id}: {e}")
            raise
