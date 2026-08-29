# Retrieval Evaluation Report

## Summary
Retrieval performance measured across BM25 lexical, dense SentenceTransformers vector search, and Reciprocal Rank Fusion (RRF).

| Mode | Recall@1 | Recall@5 | Recall@10 | MRR | nDCG@10 | Exact Anchor Hit |
|---|---|---|---|---|---|---|
| BM25 Only | 0.6562 | 0.9896 | 1.0 | 0.7569 | 0.8194 | 1.0 |
| Dense Only | 0.5625 | 0.9792 | 1.0 | 0.7065 | 0.7788 | 0.9375 |
| **Hybrid RRF** | **0.5729** | **0.9896** | **1.0** | **0.7188** | **0.7916** | **1.0** |
