"""
Structured LLM response schemas
"""
from app.schemas.structured.categorization import (
    CategorizationResponse,
    PageCategorizationResponse
)
from app.schemas.structured.merge_decision import MergeDecision
from app.schemas.structured.filename import FilenameGenerationResponse
from app.schemas.structured.insight import InsightData

__all__ = [
    "CategorizationResponse",
    "PageCategorizationResponse",
    "MergeDecision",
    "FilenameGenerationResponse",
    "InsightData",
]
