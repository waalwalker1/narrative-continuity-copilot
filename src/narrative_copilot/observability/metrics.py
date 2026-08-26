"""
Prometheus metrics definitions for Narrative Continuity Copilot.
"""

from prometheus_client import Counter, Histogram

# Histograms
manuscript_import_seconds = Histogram(
    "manuscript_import_seconds",
    "Time taken to parse and segment manuscript",
    ["format"],
)

index_job_seconds = Histogram(
    "index_job_seconds",
    "Time taken to complete an indexing job",
    ["mode"],  # full vs incremental
)

embedding_batch_seconds = Histogram(
    "embedding_batch_seconds",
    "Time spent computing dense embeddings",
)

retrieval_seconds = Histogram(
    "retrieval_seconds",
    "Time spent executing retrieval queries",
    ["retrieval_mode"],
)

retrieval_results_count = Histogram(
    "retrieval_results_count",
    "Number of retrieved evidence results returned",
    buckets=[1, 3, 5, 10, 20, 50],
)

memory_extraction_seconds = Histogram(
    "memory_extraction_seconds",
    "Time spent extracting structured story memory",
)

continuity_check_seconds = Histogram(
    "continuity_check_seconds",
    "Time spent verifying narrative continuity",
)

# Counters
alerts_created_total = Counter(
    "alerts_created_total",
    "Total continuity alerts generated",
    ["conflict_class"],
)

alerts_resolved_total = Counter(
    "alerts_resolved_total",
    "Total continuity alerts resolved or marked intentional by author",
    ["action_type"],
)

anchor_revalidation_total = Counter(
    "anchor_revalidation_total",
    "Total anchor re-validation operations performed",
    ["status"],
)

anchor_revalidation_failures_total = Counter(
    "anchor_revalidation_failures_total",
    "Total anchor invalidation events on manuscript edit",
)

llm_calls_total = Counter(
    "llm_calls_total",
    "Total calls made to LLM provider",
    ["provider", "task"],
)

llm_schema_failures_total = Counter(
    "llm_schema_failures_total",
    "Total LLM responses failing output schema validation",
    ["provider"],
)
