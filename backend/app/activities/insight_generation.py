"""
Insight Generation Activity - Create XML insight reports
"""
import logging
from datetime import datetime
from typing import Dict, Any
from xml.etree import ElementTree as ET
from xml.dom import minidom
from temporalio import activity
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import async_session_maker
from app.models import Job, Document, PromptTemplate, APICallLog
from app.services.llm_service import llm_service
from app.schemas.structured import InsightData

logger = logging.getLogger(__name__)


@activity.defn(name="generate_insight_report")
async def generate_insight_report(job_id: str) -> str:
    """
    Generate XML insight report for completed job.

    Args:
        job_id: Job UUID

    Returns:
        XML content as string
    """
    activity.heartbeat("Generating insight report")

    async with async_session_maker() as db:
        try:
            # Get job with documents
            result = await db.execute(
                select(Job).where(Job.id == job_id)
            )
            job = result.scalar_one_or_none()

            if not job:
                raise ValueError(f"Job {job_id} not found")

            # Get all documents with eager loading of category relationship
            documents_result = await db.execute(
                select(Document)
                .options(selectinload(Document.category))
                .where(Document.job_id == job_id)
                .where(Document.merged_into_id.is_(None))  # Only non-merged docs
            )
            documents = documents_result.scalars().all()

            # Build document summaries
            doc_summaries = []
            for doc in documents:
                category_name = doc.category.name if doc.category else "Unknown"
                filename = doc.assigned_filename or doc.original_filename

                summary = f"""
Document: {filename}
Category: {category_name}
Type: {doc.file_type}
Pages: {doc.total_pages or 1}
Tokens: {doc.total_tokens}
"""
                doc_summaries.append(summary)

            full_context = "\n---\n".join(doc_summaries)

            # Check token count
            token_count = await llm_service.count_tokens(full_context)

            # Get prompt template
            template_result = await db.execute(
                select(PromptTemplate).where(
                    PromptTemplate.purpose == "insight_generation",
                    PromptTemplate.is_active == True
                )
            )
            template = template_result.scalar_one_or_none()

            if not template:
                raise ValueError("Insight generation template not found")

            # Get token limit from template (default 100k)
            token_limit = template.token_limit or 100000
            # Safe limit: 80% for input, 20% reserved for output
            safe_limit = int(token_limit * 0.8)

            logger.info(f"Token count: {token_count}, Limit: {token_limit}, Safe limit: {safe_limit}")

            activity.heartbeat("Calling LLM for insight")

            insight_data = None

            if token_count <= safe_limit:
                # Direct call - no chunking needed
                prompt = template.template.format(documents_summary=full_context)

                start_time = datetime.utcnow()

                insight_data = await llm_service.call_with_structured_output(
                    prompt=prompt,
                    response_model=InsightData,
                    model_name=template.model_name,
                    temperature=template.temperature,
                    max_tokens=template.max_tokens
                )

                duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

                # Log API call
                api_log = APICallLog(
                    api_provider="mistral" if not llm_service.use_ollama else "ollama",
                    model_name=template.model_name,
                    call_type="structured_output",
                    duration_ms=duration_ms,
                    success=True
                )
                db.add(api_log)

            else:
                # Two-stage chunking strategy
                logger.info(f"Context too large ({token_count} tokens), using two-stage chunking")

                # Stage 1: Process chunks individually
                chunks = await llm_service.chunk_text_by_tokens(full_context, safe_limit)
                logger.info(f"Split into {len(chunks)} chunks of max {safe_limit} tokens")

                partial_insights = []
                for idx, chunk in enumerate(chunks):
                    activity.heartbeat(f"Stage 1: Processing chunk {idx + 1}/{len(chunks)}")

                    prompt = template.template.format(documents_summary=chunk)

                    partial_insight = await llm_service.call_with_structured_output(
                        prompt=prompt,
                        response_model=InsightData,
                        model_name=template.model_name,
                        temperature=template.temperature,
                        max_tokens=template.max_tokens
                    )
                    partial_insights.append(partial_insight)

                logger.info(f"Stage 1 complete: {len(partial_insights)} partial insights generated")

                # Stage 2: Combine all partial insights and process again
                # Build summary of all partial insights
                combined_summary = _build_partial_insights_summary(partial_insights)
                combined_token_count = await llm_service.count_tokens(combined_summary)

                logger.info(f"Stage 2: Combined summary has {combined_token_count} tokens")

                if combined_token_count <= safe_limit:
                    # Can process combined summary directly
                    activity.heartbeat("Stage 2: Final synthesis")

                    prompt = template.template.format(documents_summary=combined_summary)

                    insight_data = await llm_service.call_with_structured_output(
                        prompt=prompt,
                        response_model=InsightData,
                        model_name=template.model_name,
                        temperature=template.temperature,
                        max_tokens=template.max_tokens
                    )
                else:
                    # Combined summary still too large - use simple merge
                    logger.warning(f"Stage 2: Combined summary still too large, using simple merge")
                    insight_data = _combine_partial_insights(partial_insights)

            # Override total documents count
            insight_data.total_documents = len(documents)

            # Build XML
            xml_content = _build_xml_report(job, documents, insight_data)

            # Store in job
            job.insight_xml = xml_content
            await db.commit()

            logger.info(f"Generated insight report: {len(xml_content)} chars")

            return xml_content

        except Exception as e:
            await db.rollback()
            logger.error(f"Insight generation failed: {e}")
            raise


def _build_partial_insights_summary(partial_insights: list) -> str:
    """
    Build a summary of all partial insights for Stage 2 processing.
    This creates a compact representation that can be re-processed with the same prompt.
    """
    summaries = []

    for idx, insight in enumerate(partial_insights):
        summary = f"""
--- Partial Insight {idx + 1} ---
Applicant: {insight.applicant_name or "Unknown"}
Application Numbers: {", ".join(insight.application_numbers) if insight.application_numbers else "None"}
Categories: {", ".join([f"{cat} ({count})" for cat, count in insight.categories_summary.items()])}
Documents: {insight.total_documents}
Pages: {insight.total_pages or 0}
Key Findings:
{chr(10).join([f"  - {finding}" for finding in insight.key_findings])}
Important Dates: {", ".join(insight.important_dates) if insight.important_dates else "None"}
"""
        summaries.append(summary)

    return "\n".join(summaries)


def _combine_partial_insights(partial_insights: list) -> InsightData:
    """Combine multiple partial insights into one (simple merge without re-processing)"""
    combined = InsightData(
        applicant_name=None,
        application_numbers=[],
        key_findings=[],
        categories_summary={},
        important_dates=[],
        total_documents=0,
        total_pages=0
    )

    for insight in partial_insights:
        # Use first non-null applicant name
        if not combined.applicant_name and insight.applicant_name:
            combined.applicant_name = insight.applicant_name

        # Merge lists (deduplicate)
        combined.application_numbers.extend(insight.application_numbers)
        combined.application_numbers = list(set(combined.application_numbers))

        combined.key_findings.extend(insight.key_findings)

        combined.important_dates.extend(insight.important_dates)
        combined.important_dates = list(set(combined.important_dates))

        # Merge category counts
        for category, count in insight.categories_summary.items():
            combined.categories_summary[category] = combined.categories_summary.get(category, 0) + count

        combined.total_documents += insight.total_documents
        if insight.total_pages:
            combined.total_pages = (combined.total_pages or 0) + insight.total_pages

    return combined


def _build_xml_report(job: Job, documents: list, insight: InsightData) -> str:
    """Build XML report from insight data"""
    root = ET.Element("DocumentProcessingReport")

    # Job info
    job_info = ET.SubElement(root, "JobInformation")
    ET.SubElement(job_info, "JobID").text = str(job.id)
    ET.SubElement(job_info, "JobType").text = job.type.value
    ET.SubElement(job_info, "ProcessedAt").text = datetime.utcnow().isoformat()
    ET.SubElement(job_info, "OriginalFile").text = job.original_filename

    # Summary
    summary = ET.SubElement(root, "Summary")
    ET.SubElement(summary, "TotalDocuments").text = str(insight.total_documents)
    if insight.total_pages:
        ET.SubElement(summary, "TotalPages").text = str(insight.total_pages)
    if insight.applicant_name:
        ET.SubElement(summary, "ApplicantName").text = insight.applicant_name

    # Application numbers
    if insight.application_numbers:
        app_numbers = ET.SubElement(root, "ApplicationNumbers")
        for num in insight.application_numbers:
            ET.SubElement(app_numbers, "Number").text = num

    # Categories
    categories = ET.SubElement(root, "Categories")
    for category, count in insight.categories_summary.items():
        cat_elem = ET.SubElement(categories, "Category")
        ET.SubElement(cat_elem, "Name").text = category
        ET.SubElement(cat_elem, "Count").text = str(count)

    # Key findings
    if insight.key_findings:
        findings = ET.SubElement(root, "KeyFindings")
        for finding in insight.key_findings:
            ET.SubElement(findings, "Finding").text = finding

    # Important dates
    if insight.important_dates:
        dates = ET.SubElement(root, "ImportantDates")
        for date in insight.important_dates:
            ET.SubElement(dates, "Date").text = date

    # Documents list
    docs = ET.SubElement(root, "Documents")
    for doc in documents:
        doc_elem = ET.SubElement(docs, "Document")
        ET.SubElement(doc_elem, "OriginalFilename").text = doc.original_filename
        ET.SubElement(doc_elem, "AssignedFilename").text = doc.assigned_filename or ""
        ET.SubElement(doc_elem, "Category").text = doc.category.name if doc.category else "Unknown"
        ET.SubElement(doc_elem, "FileType").text = doc.file_type
        ET.SubElement(doc_elem, "Tokens").text = str(doc.total_tokens)

    # Pretty print
    xml_string = ET.tostring(root, encoding="unicode")
    dom = minidom.parseString(xml_string)
    pretty_xml = dom.toprettyxml(indent="  ")

    return pretty_xml
