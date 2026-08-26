# ADR-003: Elasticsearch Hybrid Retrieval via Reciprocal Rank Fusion (RRF)

## Status
Accepted

## Context
Lexical BM25 search excels at exact character names, unique fantasy terms, and specific dates, but misses synonyms and paraphrase. Dense embeddings capture semantic similarity but struggle with rare proper nouns and exact quotes.

## Decision
Use Elasticsearch 8 with Reciprocal Rank Fusion (RRF) combining:
1. BM25 lexical retrieval over normalized manuscript blocks.
2. Dense cosine vector search using SentenceTransformers `all-MiniLM-L6-v2` embeddings.
3. RRF formula: $RRF(d) = \sum_{m \in M} \frac{1}{60 + r_m(d)}$.

## Consequences
- Maximizes Recall@k and MRR across both keyword-dense queries and semantic narrative queries.
- Exposes score decomposition for transparent debugging.
