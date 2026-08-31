# Release Validation Evidence

## Environment Specifications
- **Benchmark Source Commit**: `447fe4c4935e691167c00eef3c2ecb082a067914`
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
- **BM25 Only Recall@5**: 99.0% (MRR: 0.7569)
- **Dense Only Recall@5**: 100.0% (MRR: 0.7948)
- **Hybrid RRF Recall@5**: **99.0%** (MRR: **0.7639**, nDCG@10: **0.8241**)
- **Exact Anchor Hit Rate**: 100.0%

### End-to-End Continuity Detection
- **Precision**: 99.4%
- **Recall**: 88.6%
- **F1 Score**: 93.7%
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
- **Indexing Throughput**: ~11,938 words/sec
- **Retrieval Latency (p50 / p95)**: 20.3 ms / 23.9 ms
- **Long-Distance Evidence Recall**: 100.0%
<!-- METRIC_BLOCK_END -->

### Software Quality & Test Gates
- **Backend Unit & Property Tests**: 100% passing (Hypothesis + Pytest)
- **Frontend Unit Tests**: 100% passing (Vitest + Vue Test Utils)
- **Browser E2E Tests**: 100% passing (Playwright Chromium)
- **Static Analysis**: Ruff (0 errors), mypy strict (0 errors), eslint & vue-tsc (0 errors)
- **Security Audits**: Bandit (0 high/medium issues), pip-audit (clean), npm audit gate (accepted risks documented)
- **Docker E2E Transaction**: 100% passing end-to-end containerized run

## Provider Verification Status
- `DeterministicFixtureLLMProvider`: `IMPLEMENTED_AND_TESTED`
- `SentenceTransformerEmbeddingProvider`: `IMPLEMENTED_AND_TESTED`
- `VertexAIProvider`: `CONTRACT_TESTED`
- `ElasticsearchEngine`: `IMPLEMENTED_AND_TESTED`
