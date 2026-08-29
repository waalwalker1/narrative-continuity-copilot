# Ablation Studies Report

| Configuration | Description | Continuity F1 | Delta F1 | Retrieval Recall@5 |
|---|---|---|---|---|
| A_bm25_only | Lexical BM25 retrieval without dense semantic vectors | 89.7% | +0.00 | 99.0% |
| B_dense_only | Dense vector search without BM25 keyword matching | 89.7% | +0.00 | 97.9% |
| C_hybrid_retrieval | Reciprocal Rank Fusion of BM25 and dense embeddings | 89.7% | +0.00 | 99.0% |
| D_hybrid_plus_alias_expansion | Hybrid retrieval with alias and nickname graph expansion | 89.7% | +0.00 | 99.0% |
| E_hybrid_plus_structured_story_memory | Hybrid retrieval combined with structured memory entity filters | 89.7% | +0.00 | 99.0% |
| F_without_temporal_scoping | System without timeline event and temporal scope filters | 89.7% | +0.00 | 99.0% |
| G_without_narrative_epistemic_scoping | System treating dreams, rumors, and POV beliefs as global canon | 82.1% | -0.08 | 99.0% |
| H_without_evidence_critic | System without pre-alert evidence validation gate | 89.7% | +0.00 | 99.0% |
| I_without_author_intentionality_rules | System without author suppression and exception persistence | 89.7% | +0.00 | 99.0% |
| J_long_context_baseline | Direct un-indexed context baseline over raw manuscript chunks | 89.7% | +0.00 | 99.0% |
| K_full_system | Full hybrid retrieval, structured memory, epistemic reasoning, critic, and validator | 89.7% | +0.00 | 99.0% |
