# Retrieval Evaluation Report

## Summary
Retrieval performance measured across BM25 lexical, dense SentenceTransformers vector search, and Reciprocal Rank Fusion (RRF).

| Mode | Recall@1 | Recall@5 | Recall@10 | MRR | nDCG@10 | Exact Anchor Hit |
|---|---|---|---|---|---|---|
| BM25 Only | 0.6667 | 1.0 | 1.0 | 0.8212 | 0.8674 | 0.8229 |
| Dense Only | 0.5625 | 0.9896 | 1.0 | 0.7387 | 0.8049 | 0.9167 |
| **Hybrid RRF** | **0.5833** | **1.0** | **1.0** | **0.7821** | **0.8387** | **0.8646** |
