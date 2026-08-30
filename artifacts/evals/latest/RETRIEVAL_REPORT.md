# Retrieval Evaluation Report

## Summary
Retrieval performance measured across BM25 lexical, dense SentenceTransformers vector search, and Reciprocal Rank Fusion (RRF).

| Mode | Recall@1 | Recall@5 | Recall@10 | MRR | nDCG@10 | Exact Anchor Hit |
|---|---|---|---|---|---|---|
| BM25 Only | 0.6562 | 0.9896 | 1.0 | 0.7569 | 0.8194 | 1.0 |
| Dense Only | 0.75 | 1.0 | 1.0 | 0.7948 | 0.8461 | 0.9271 |
| **Hybrid RRF** | **0.6562** | **0.9896** | **1.0** | **0.7639** | **0.8241** | **1.0** |
