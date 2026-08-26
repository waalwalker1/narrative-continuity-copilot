"""
Continuity schemas and adjudication models.
"""

from typing import Literal

from pydantic import BaseModel, Field

from narrative_copilot.schemas import ConflictClass


class CandidatePair(BaseModel):
    pair_id: str
    project_id: str
    revision_id: str
    fact_id_a: str
    fact_id_b: str
    subject_entity_id: str
    predicate: str
    value_a: str | None = None
    value_b: str | None = None
    anchor_id_a: str
    anchor_id_b: str
    snippet_a: str
    snippet_b: str
    chapter_id_a: str
    chapter_id_b: str
    block_id_a: str
    block_id_b: str
    narrative_scope_a: str = "GLOBAL_CANON"
    narrative_scope_b: str = "GLOBAL_CANON"
    epistemic_status_a: str = "OBSERVED"
    epistemic_status_b: str = "OBSERVED"
    temporal_scope_a: str = "DEFAULT"
    temporal_scope_b: str = "DEFAULT"


class AdjudicationResult(BaseModel):
    is_contradiction: bool
    conflict_class: ConflictClass
    confidence: float = 0.95
    confidence_category: Literal["HIGH", "MEDIUM", "LOW", "INFORMATIONAL"] = "HIGH"
    explanation: str
    alternate_interpretations: list[str] = Field(default_factory=list)
    requires_author_review: bool = True
    cited_anchor_ids: list[str] = Field(default_factory=list)
    missing_context: str | None = None


class DeterministicPreconditionResult(BaseModel):
    passed: bool
    rejection_reason: str | None = None
