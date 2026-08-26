# Benchmark Evaluation Methodology

## Dataset Construction
To ensure evaluation integrity without copyright concerns, the benchmark uses a deterministic synthetic story generator producing:
- **36 Multi-Chapter Story Packs** across 6 genres (Fantasy, Mystery, Historical Drama, Sci-Fi, Romance, Gothic Thriller).
- **216 Ground-Truth Continuity Cases** covering the complete 12-class taxonomy.

## Story-Level Partitions
To prevent data and threshold leakage, cases are grouped by story pack:
- **Train / Development Partition**: 25 Story Packs (150 Cases)
- **Held-Out Evaluation Partition**: 11 Story Packs (66 Cases)

## Metric Definitions
1. **Retrieval Recall@k**: Percentage of cases where the target evidence snippet appears in top-$k$ search results.
2. **Mean Reciprocal Rank (MRR)**: Average reciprocal rank of the first relevant evidence chunk.
3. **Continuity Precision & Recall**: True positives / (True positives + False positives) and True positives / (True positives + False negatives).
4. **Macro F1**: Unweighted mean of F1 scores across all 12 continuity contradiction classes.
5. **Intentional Ambiguity False Positive Rate**: False positive rate specifically on intentional ambiguities, rumors, dreams, and character lies.
6. **Citation Provenance Validity**: Percentage of generated alerts whose cited evidence anchors strictly exist in the manuscript.
7. **Unsupported Claim Rate**: Rate of alerts containing factual claims not grounded in cited anchors (target: 0.0%).
