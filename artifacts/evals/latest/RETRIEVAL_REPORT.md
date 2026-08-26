# Retrieval Evaluation Report

## Summary
Retrieval performance measured across BM25 lexical, dense SentenceTransformers vector search, and Reciprocal Rank Fusion (RRF).

| Mode | Recall@1 | Recall@5 | Recall@10 | MRR | nDCG@10 | Exact Anchor Hit |
|---|---|---|---|---|---|---|
| BM25 Only | 0.8333 | 1.0 | 1.0 | 0.887 | 0.9151 | 1.0 |
| Dense Only | 0.625 | 1.0 | 1.0 | 0.7405 | 0.8036 | 1.0 |
| **Hybrid RRF** | **0.7917** | **1.0** | **1.0** | **0.8619** | **0.8961** | **1.0** |
