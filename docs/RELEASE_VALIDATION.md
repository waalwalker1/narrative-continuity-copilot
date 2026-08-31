# Release Validation Evidence

## Environment Specifications
- **Benchmark Source Commit**: `6569aa5dd47d76318fe4ea455ae540b439ac1dac`
- **Python Runtime**: Python 3.12 (CPython x86_64/arm64)
- **Node Runtime**: Node.js v20.x
- **Search Backend**: Elasticsearch 8.14.0 (BM25 + 384-dimensional dense vectors)
- **Primary Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` (Dimension 384)
- **Primary Inference Adapter**: `DeterministicFixtureLLMProvider` (Local canonical) / `VertexAIProvider` (Cloud adapter)

## Dataset & Benchmark Integrity
- **Total Story Packs**: 48 multi-chapter packs (Fantasy, Mystery, Historical Drama, Sci-Fi, Romance, Gothic Thriller)
- **Total Benchmark Cases**: 576 test cases
- **Story-Level Splits**: 32 Train Story Packs (384 cases) / 16 Held-Out Evaluation Story Packs (192 cases)
- **Contradiction Classes**: Full coverage across all 12 classes of narrative continuity taxonomy

## Measured Benchmark Results
*All metrics generated deterministically by `evals/runners/run_all.py` and synchronized into `artifacts/evals/latest/summary.json`.*

<!-- METRIC_BLOCK_START -->
### Retrieval Metrics
- **BM25 Only Recall@5**: 99.0% (MRR: 0.8226)
- **Dense Only Recall@5**: 100.0% (MRR: 0.7948)
- **Hybrid RRF Recall@5**: **99.0%** (MRR: **0.7847**, nDCG@10: **0.8403**)
- **Exact Anchor Hit Rate**: 100.0%

### End-to-End Continuity Detection
- **Precision**: 90.7%
- **Recall**: 88.6%
- **F1 Score**: 89.7%
- **Macro F1 Score**: 86.7%
- **Intentional Ambiguity FPR**: 0.0% (Dreams, rumors, lies, and POV beliefs correctly routed)
- **Citation Provenance Validity**: 100.0% (Zero hallucinated or missing anchor citations)
- **Unsupported Factual Claim Rate**: 0.0%

### Anchor Stability & Edit Re-anchoring
- **Operations Evaluated**: 220 edit mutations
- **Expected-Outcome Accuracy**: 88.6%
- **Exact Match Accuracy**: 100.0%
- **Realignment Accuracy**: 79.7%
- **Transfer Accuracy**: 100.0%
- **Invalidation Accuracy**: 100.0%
- **Invalidation Precision**: 49.0%
- **False Re-anchor Rate**: 0.0%

### Prompt-Injection Red-Teaming
- **Total Adversarial Fixtures**: 40/40 passed (100.0% pass rate)
- **Security Boundary Invariants**: Complete isolation between untrusted manuscript prose and system instruction roles.

### Long Manuscript Benchmark (96,755 words)
- **Indexing Throughput**: ~9,153 words/sec
- **Retrieval Latency (p50 / p95)**: 13.3 ms / 17.9 ms
- **Long-Distance Evidence Recall**: 100.0%
<!-- METRIC_BLOCK_END -->

### Software Quality & Test Gates
- **Backend Unit & Property Tests**: 100% passing (Hypothesis + Pytest)
- **Frontend Unit Tests**: 100% passing (Vitest + Vue Test Utils)
- **Browser E2E Tests**: 100% passing (Playwright Chromium)
- **Static Analysis**: Ruff (0 errors), mypy strict (0 errors), eslint & vue-tsc (0 errors)
- **Security Audits**: Bandit (0 high/medium issues), pip-audit (clean), npm audit gate (accepted risks documented)
- **Docker E2E Transaction**: 100% passing end-to-end containerized run

### Auxiliary Evaluation Limitations
- **Incremental Indexing & Stale Memory**: Stale-fact memory invalidation is measured on applicable edit scenarios (10/100). Fresh-fact discovery recall is conservative (10%) under the deterministic reference extractor.
- **Subsystem Ablations**: Subsystems F (temporal scoping) and H (evidence critic) show no measurable delta on the current 16 held-out story packs because gold evaluation cases do not contain temporal masking or malformed citation anchors. Subsystem I (author preconditions) is reported as `NOT_MEASURED` on the generic benchmark because held-out packs evaluate cold manuscripts with no pre-existing author overrides.

## Provider Verification Status
- `DeterministicFixtureLLMProvider`: `IMPLEMENTED_AND_TESTED`
- `SentenceTransformerEmbeddingProvider`: `IMPLEMENTED_AND_TESTED`
- `VertexAIProvider`: `CONTRACT_TESTED`
- `ElasticsearchEngine`: `IMPLEMENTED_AND_TESTED`
