# System & Subsystem Ablations Report

## 1. Measured End-to-End Continuity System Ablations

| Configuration | Description | Continuity F1 | Delta vs Full | Precision | Recall | Status |
|---|---|---|---|---|---|---|
| **Full Reference System** | Full hybrid retrieval, structured memory, epistemic reasoning, critic, and validator | 93.7% | +0.00 | 99.4% | 88.6% | `MEASURED` |
| **Without Epistemic Scoping** | System treating dreams, rumors, and POV beliefs as global canon | 82.1% | -0.12 | 76.5% | 88.6% | `MEASURED` |
| **Raw Context Baseline** | Direct un-indexed context baseline over raw recent manuscript chunks (first 5 blocks only) | 94.0% | +0.00 | 100.0% | 88.6% | `MEASURED` |

## 2. Measured Retrieval Mode Comparisons (Canonical Evaluator)

| Retrieval Mode | Recall@1 | Recall@5 | Recall@10 | MRR | nDCG@10 | Exact Anchor Hit |
|---|---|---|---|---|---|---|
| **BM25 Lexical Retrieval Only** | 65.6% | 99.0% | 100.0% | 0.7569 | 0.8194 | 100.0% |
| **Dense Vector Search Only** | 75.0% | 100.0% | 100.0% | 0.7948 | 0.8461 | 92.7% |
| **Hybrid RRF Retrieval** | 65.6% | 99.0% | 100.0% | 0.7639 | 0.8241 | 100.0% |
| **Hybrid + Alias Expansion** | 65.6% | 99.0% | 100.0% | 0.7639 | 0.8241 | 100.0% |
| **Hybrid + Story Memory Filter** | 65.6% | 99.0% | 100.0% | 0.7639 | 0.8241 | 100.0% |

## 3. Subsystem Ablations (Auxiliary / Not Measured on Held-Out Cohort)

| Component | Measurement Status | Diagnostic Reason |
|---|---|---|
| **Temporal Scoping (F)** | `NO_MEASURABLE_DELTA_ON_CURRENT_COHORT` | No temporal order contradictions are masked by time filtering in current 16 held-out story packs. |
| **Evidence Critic (H)** | `NO_MEASURABLE_DELTA_ON_CURRENT_COHORT` | Current gold evaluation fixtures contain well-formed citation anchors that pass critic validation. |
| **Author Preconditions (I)** | `NOT_MEASURED` | Not measured on main corpus because no author decision overrides are persisted in the cold held-out story packs. |
