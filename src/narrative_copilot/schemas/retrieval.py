"""
Retrieval and Search schemas for Narrative Continuity Copilot.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RetrievalMode(str, Enum):
    BM25_ONLY = "BM25_ONLY"
    DENSE_ONLY = "DENSE_ONLY"
    HYBRID_RRF = "HYBRID_RRF"
    HYBRID_EXPANDED = "HYBRID_EXPANDED"
    MEMORY_FILTERED = "MEMORY_FILTERED"


class SearchTarget(str, Enum):
    MANUSCRIPT_CHUNKS = "manuscript_chunks"
    STORY_MEMORY = "story_memory"
    ALL = "all"


class RetrievalQuery(BaseModel):
    query: str
    project_id: str
    revision_id: str | None = None
    retrieval_mode: RetrievalMode = RetrievalMode.HYBRID_RRF
    search_target: SearchTarget = SearchTarget.MANUSCRIPT_CHUNKS
    entity_filter_ids: list[str] = Field(default_factory=list)
    chapter_filter_ids: list[str] = Field(default_factory=list)
    time_scope: str | None = None
    top_k: int = 10
    include_scores: bool = True


class ScoreDecomposition(BaseModel):
    bm25_score: float = 0.0
    bm25_rank: int | None = None
    dense_score: float = 0.0
    dense_rank: int | None = None
    rrf_score: float = 0.0
    rerank_score: float | None = None


class RetrievalResultItem(BaseModel):
    doc_id: str
    target: SearchTarget
    anchor_id: str
    chapter_id: str
    block_id: str
    text_snippet: str
    score: float
    score_decomposition: ScoreDecomposition
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalResponse(BaseModel):
    project_id: str
    query: str
    retrieval_mode: RetrievalMode
    results: list[RetrievalResultItem] = Field(default_factory=list)
    total_hits: int = 0
    query_latency_ms: float = 0.0
