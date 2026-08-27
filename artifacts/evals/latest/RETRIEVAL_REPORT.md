# Retrieval Evaluation Report

## Summary
Retrieval performance measured across BM25 lexical, dense SentenceTransformers vector search, and Reciprocal Rank Fusion (RRF).

| Mode | Recall@1 | Recall@5 | Recall@10 | MRR | nDCG@10 | Exact Anchor Hit |
|---|---|---|---|---|---|---|
| BM25 Only | 0.6528 | 0.9861 | 1.0 | 0.805 | 0.8547 | 1.0 |
| Dense Only | 0.5833 | 0.9861 | 1.0 | 0.7573 | 0.8189 | 1.0 |
| **Hybrid RRF** | **0.625** | **0.9861** | **1.0** | **0.8002** | **0.8516** | **1.0** |
