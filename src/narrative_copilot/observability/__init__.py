"""
Observability package.
"""

from narrative_copilot.observability.logging import log_privacy_safe, logger
from narrative_copilot.observability.metrics import (
    alerts_created_total,
    alerts_resolved_total,
    anchor_revalidation_failures_total,
    anchor_revalidation_total,
    continuity_check_seconds,
    embedding_batch_seconds,
    index_job_seconds,
    llm_calls_total,
    llm_schema_failures_total,
    manuscript_import_seconds,
    memory_extraction_seconds,
    retrieval_results_count,
    retrieval_seconds,
)
from narrative_copilot.observability.tracing import trace_span, tracer

__all__ = [
    "alerts_created_total",
    "alerts_resolved_total",
    "anchor_revalidation_failures_total",
    "anchor_revalidation_total",
    "continuity_check_seconds",
    "embedding_batch_seconds",
    "index_job_seconds",
    "llm_calls_total",
    "llm_schema_failures_total",
    "log_privacy_safe",
    "logger",
    "manuscript_import_seconds",
    "memory_extraction_seconds",
    "retrieval_results_count",
    "retrieval_seconds",
    "trace_span",
    "tracer",
]
