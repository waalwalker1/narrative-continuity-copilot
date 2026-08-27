# Ablation Studies Report

| Configuration | Description | Continuity F1 | Delta F1 |
|---|---|---|---|
| A_bm25_only | Lexical BM25 retrieval without dense semantic vectors | 100.0% | +0.00 |
| B_dense_only | Dense vector search without BM25 keyword matching | 100.0% | +0.00 |
| C_hybrid_retrieval | Reciprocal Rank Fusion of BM25 and dense embeddings | 100.0% | +0.00 |
| D_hybrid_plus_alias_expansion | Hybrid retrieval with alias and nickname graph expansion | 100.0% | +0.00 |
| E_hybrid_plus_structured_story_memory | Hybrid retrieval combined with structured memory entity filters | 100.0% | +0.00 |
| F_without_temporal_scoping | System without timeline event and temporal scope filters | 100.0% | +0.00 |
| G_without_narrative_epistemic_scoping | System treating dreams, rumors, and POV beliefs as global canon | 87.5% | -0.12 |
| H_without_evidence_critic | System without pre-alert evidence validation gate | 100.0% | +0.00 |
| I_without_author_intentionality_rules | System without author suppression and exception persistence | 100.0% | +0.00 |
| J_long_context_baseline | Direct un-indexed context baseline over raw manuscript chunks | 100.0% | +0.00 |
| K_full_system | Full hybrid retrieval, structured memory, epistemic reasoning, critic, and validator | 100.0% | +0.00 |
