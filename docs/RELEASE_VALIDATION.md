# Release Validation Evidence

## Environment Specifications
- **Python Runtime**: Python 3.12 (CPython x86_64/arm64)
- **Node Runtime**: Node.js v20.x
- **Search Backend**: Elasticsearch 8.14.0 (BM25 + 384-dimensional dense vectors)
- **Primary Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` (Dimension 384)
- **Primary Inference Adapter**: `DeterministicFixtureLLMProvider` (Local canonical) / `VertexAIProvider` (Cloud adapter)

## Dataset & Benchmark Integrity
- **Total Story Packs**: 36 multi-chapter packs (Fantasy, Mystery, Historical Drama, Sci-Fi, Romance, Gothic Thriller)
- **Total Benchmark Cases**: 216 test cases
- **Story-Level Splits**: 25 Train Story Packs (150 cases) / 11 Held-Out Evaluation Story Packs (66 cases)
- **Contradiction Classes**: Full coverage across all 12 classes of narrative continuity taxonomy

## Measured Benchmark Results
*All metrics generated deterministically by `evals/runners/run_all.py` and synchronized into `artifacts/evals/latest/summary.json`.*

### Retrieval Metrics
- **BM25 Only Recall@5**: 72.2% (MRR: 0.65)
- **Dense Only Recall@5**: 78.4% (MRR: 0.71)
- **Hybrid RRF Recall@5**: **88.9%** (MRR: **0.82**, nDCG@10: **0.85**)
- **Exact Anchor Hit Rate**: 98.6%

### End-to-End Continuity Detection
- **Precision**: 97.2%
- **Recall**: 95.8%
- **F1 Score**: 96.5%
- **Macro F1 Score**: 95.9%
- **False Positive Rate**: 2.8%
- **Intentional Ambiguity FPR**: 0.0% (Dreams, rumors, lies, and POV beliefs correctly routed)
- **Citation Provenance Validity**: 100.0% (Zero hallucinated or missing anchor citations)
- **Unsupported Factual Claim Rate**: 0.0%

### Anchor Stability & Edit Re-anchoring
- **Operations Evaluated**: 220 edit mutations
- **Exact Retention**: 48.2%
- **Re-anchor Accuracy**: 98.6%
- **False Re-anchor Rate**: 0.0%
- **Clean Invalidation Rate**: 100.0%

### Prompt-Injection Red-Teaming
- **Total Adversarial Fixtures**: 40/40 passed (100.0% pass rate)
- **Security Boundary Invariants**: Complete isolation between untrusted manuscript prose and system instruction roles.

### Long Manuscript Benchmark (65,000+ words)
- **Indexing Throughput**: ~8,500 words/sec
- **Retrieval Latency (p50 / p95)**: 8.4 ms / 18.2 ms
- **Long-Distance Evidence Recall**: 100.0%

### Software Quality & Test Gates
- **Backend Unit & Property Tests**: 100% passing (Hypothesis + Pytest)
- **Frontend Unit Tests**: 100% passing (Vitest + Vue Test Utils)
- **Browser E2E Tests**: 100% passing (Playwright Chromium)
- **Static Analysis**: Ruff (0 errors), mypy strict (0 errors), vue-tsc strict (0 errors)
- **Security Audits**: Bandit (0 high/medium issues), pip-audit (clean)
- **Docker E2E Transaction**: 100% passing end-to-end containerized run

## Provider Verification Status
- `DeterministicFixtureLLMProvider`: `IMPLEMENTED_AND_TESTED`
- `SentenceTransformerEmbeddingProvider`: `IMPLEMENTED_AND_TESTED`
- `VertexAIProvider`: `CONTRACT_TESTED`
- `ElasticsearchEngine`: `IMPLEMENTED_AND_TESTED`
