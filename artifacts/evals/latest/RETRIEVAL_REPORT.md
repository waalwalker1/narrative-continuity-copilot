# Hybrid Retrieval & Ranking Evaluation Report

## Summary
Retrieval performance measured across BM25 lexical, dense SentenceTransformers vector search, and Reciprocal Rank Fusion (RRF).

| Mode | Recall@1 | Recall@5 | Recall@10 | MRR | nDCG@10 | Exact Anchor Hit |
|---|---|---|---|---|---|---|
| BM25 Only | 0.6979 | 0.9896 | 1.0 | 0.8226 | 0.8679 | 1.0 |
| Dense Only | 0.75 | 1.0 | 1.0 | 0.7948 | 0.8461 | 0.9271 |
| **Hybrid RRF** | **0.625** | **0.9896** | **1.0** | **0.7847** | **0.8403** | **1.0** |
