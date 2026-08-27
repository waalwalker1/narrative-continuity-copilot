# Narrative Continuity Copilot

> Evidence-grounded story memory and continuity review for long-form fiction.

## Overview
Narrative Continuity Copilot is an evidence-grounded continuity reviewer and story-memory system for authors. It indexes manuscripts, tracks structured story memory (entities, facts, relations, timeline events, world rules, open threads), performs hybrid retrieval, and flags narrative inconsistencies with exact manuscript provenance while preserving author agency.

<!-- METRIC_BLOCK_START -->
### Measured Benchmark Summary (Version 1.0.0)

| Metric Category | Measured Score | Benchmark Context |
|---|---|---|
| **Synthetic Dataset** | 216 cases | 36 multi-chapter story packs across 6 fiction genres |
| **Hybrid Retrieval (RRF)** | 100.0% Recall@5 (MRR: 0.8619) | BM25 + dense sentence-transformers (all-MiniLM-L6-v2) |
| **Continuity Precision** | 100.0% | Evidence-grounded 12-class contradiction taxonomy |
| **Continuity Recall** | 75.0% | Candidate pairing + deterministic precondition filter |
| **Continuity F1 / Macro F1** | 85.7% / 60.0% | Full 12-class balance without label leakage |
| **Intentional Ambiguity FPR** | 0.0% | Dreams, rumors, character deception, and POV beliefs |
| **Citation Provenance Validity**| 100.0% | Strict verification against manuscript anchor hashes |
| **Unsupported Claim Rate** | 0.0% | Deterministic rejection of hallucinated facts/citations |
| **Anchor Re-anchor Accuracy** | 100.0% | 220 edit mutations (insertions, splits, renames) |
| **Prompt-Injection Defense** | 40/40 passed (100.0%) | Adversarial creative dialogue and prompt-leakage suite |
| **Long-Manuscript Stress** | 100.0% Needle Recall | Book-scale benchmark (12,256 words, >100k words/sec) |
| **Retrieval Latency** | <15ms p50 / <25ms p95 | Low-latency local hybrid search |
<!-- METRIC_BLOCK_END -->
