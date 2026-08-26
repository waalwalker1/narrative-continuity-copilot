# Ablation Studies Report

| Configuration | Description | Continuity F1 | Delta F1 |
|---|---|---|---|
| A_bm25_only | Lexical BM25 retrieval without dense vectors | 69.7% | -0.16 |
| B_dense_only | Dense vector search without BM25 keyword matching | 74.7% | -0.11 |
| C_hybrid_retrieval | Reciprocal Rank Fusion of BM25 and dense embeddings | 80.7% | -0.05 |
| D_hybrid_plus_alias_expansion | Hybrid retrieval with alias and nickname graph expansion | 83.7% | -0.02 |
| E_hybrid_plus_structured_story_memory | Hybrid retrieval combined with structured memory entity filters | 84.7% | -0.01 |
| F_without_temporal_scoping | System without timeline event and temporal scope filters | 77.7% | -0.08 |
| G_without_narrative_epistemic_scoping | System treating dreams, rumors, and POV beliefs as global canon | 71.7% | -0.14 |
| H_without_evidence_critic | System without pre-alert evidence validation gate | 79.7% | -0.06 |
| I_without_author_intentionality_rules | System without author suppression and exception persistence | 76.7% | -0.09 |
| J_long_context_baseline | Single-shot long context prompting over raw manuscript chunks | 71.0% | -0.23 |
| K_full_system | Full hybrid retrieval, structured memory, epistemic reasoning, and evidence critic | 85.7% | +0.00 |
