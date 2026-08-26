"""
Hybrid retrieval pipeline implementing Reciprocal Rank Fusion (RRF) across BM25 and dense vector search.
"""

from typing import Any

from narrative_copilot.llm.provider import EmbeddingProvider
from narrative_copilot.retrieval.elasticsearch_client import ElasticsearchEngine
from narrative_copilot.schemas.retrieval import (
    RetrievalMode,
    RetrievalQuery,
    RetrievalResponse,
    RetrievalResultItem,
    ScoreDecomposition,
    SearchTarget,
)


class HybridRetrievalPipeline:
    """
    Orchestrates BM25, dense vector search, and RRF rank fusion.
    """

    def __init__(
        self,
        es_engine: ElasticsearchEngine,
        embedding_provider: EmbeddingProvider,
        rrf_k: int = 60,
    ) -> None:
        self.es_engine = es_engine
        self.embedding_provider = embedding_provider
        self.rrf_k = rrf_k

    async def search(self, query: RetrievalQuery) -> RetrievalResponse:
        """
        Execute hybrid search based on query parameters and retrieval mode.
        """
        project_id = query.project_id
        revision_id = query.revision_id
        text_query = query.query
        top_k = query.top_k

        # 1. Lexical BM25 search
        bm25_hits: list[tuple[dict[str, Any], float]] = []
        if query.retrieval_mode in (
            RetrievalMode.BM25_ONLY,
            RetrievalMode.HYBRID_RRF,
            RetrievalMode.HYBRID_EXPANDED,
            RetrievalMode.MEMORY_FILTERED,
        ):
            bm25_hits = self.es_engine.bm25_search_chunks(
                query=text_query,
                project_id=project_id,
                revision_id=revision_id,
                entity_ids=query.entity_filter_ids if query.entity_filter_ids else None,
                top_k=max(top_k * 2, 20),
            )

        # 2. Dense Vector search
        dense_hits: list[tuple[dict[str, Any], float]] = []
        if query.retrieval_mode in (
            RetrievalMode.DENSE_ONLY,
            RetrievalMode.HYBRID_RRF,
            RetrievalMode.HYBRID_EXPANDED,
            RetrievalMode.MEMORY_FILTERED,
        ):
            query_vector = (await self.embedding_provider.aencode([text_query]))[0]
            dense_hits = self.es_engine.vector_search_chunks(
                query_vector=query_vector,
                project_id=project_id,
                revision_id=revision_id,
                top_k=max(top_k * 2, 20),
            )

        # Handle pure modes
        if query.retrieval_mode == RetrievalMode.BM25_ONLY:
            items = []
            for rank, (doc, score) in enumerate(bm25_hits[:top_k], start=1):
                decomp = ScoreDecomposition(bm25_score=score, bm25_rank=rank, rrf_score=score)
                items.append(self._build_result_item(doc, score, decomp))
            return RetrievalResponse(
                project_id=project_id,
                query=text_query,
                retrieval_mode=query.retrieval_mode,
                results=items,
                total_hits=len(items),
            )

        if query.retrieval_mode == RetrievalMode.DENSE_ONLY:
            items = []
            for rank, (doc, score) in enumerate(dense_hits[:top_k], start=1):
                decomp = ScoreDecomposition(dense_score=score, dense_rank=rank, rrf_score=score)
                items.append(self._build_result_item(doc, score, decomp))
            return RetrievalResponse(
                project_id=project_id,
                query=text_query,
                retrieval_mode=query.retrieval_mode,
                results=items,
                total_hits=len(items),
            )

        # 3. Reciprocal Rank Fusion (RRF)
        fused_scores: dict[str, float] = {}
        bm25_ranks: dict[str, tuple[int, float]] = {}
        dense_ranks: dict[str, tuple[int, float]] = {}
        doc_lookup: dict[str, dict[str, Any]] = {}

        for rank, (doc, score) in enumerate(bm25_hits, start=1):
            doc_id = doc["chunk_id"]
            doc_lookup[doc_id] = doc
            bm25_ranks[doc_id] = (rank, score)
            fused_scores[doc_id] = fused_scores.get(doc_id, 0.0) + (1.0 / (self.rrf_k + rank))

        for rank, (doc, score) in enumerate(dense_hits, start=1):
            doc_id = doc["chunk_id"]
            doc_lookup[doc_id] = doc
            dense_ranks[doc_id] = (rank, score)
            fused_scores[doc_id] = fused_scores.get(doc_id, 0.0) + (1.0 / (self.rrf_k + rank))

        # Sort by fused score descending
        sorted_doc_ids = sorted(
            fused_scores.keys(), key=lambda did: fused_scores[did], reverse=True
        )

        final_items: list[RetrievalResultItem] = []
        for did in sorted_doc_ids[:top_k]:
            doc = doc_lookup[did]
            f_score = fused_scores[did]
            bm25_rank, bm25_score = bm25_ranks.get(did, (None, 0.0))
            dense_rank, dense_score = dense_ranks.get(did, (None, 0.0))

            decomp = ScoreDecomposition(
                bm25_score=bm25_score,
                bm25_rank=bm25_rank,
                dense_score=dense_score,
                dense_rank=dense_rank,
                rrf_score=round(f_score, 6),
            )
            final_items.append(self._build_result_item(doc, f_score, decomp))

        return RetrievalResponse(
            project_id=project_id,
            query=text_query,
            retrieval_mode=query.retrieval_mode,
            results=final_items,
            total_hits=len(final_items),
        )

    def _build_result_item(
        self,
        doc: dict[str, Any],
        score: float,
        decomp: ScoreDecomposition,
    ) -> RetrievalResultItem:
        return RetrievalResultItem(
            doc_id=doc.get("chunk_id", ""),
            target=SearchTarget.MANUSCRIPT_CHUNKS,
            anchor_id=doc.get("anchor_id", ""),
            chapter_id=doc.get("chapter_id", ""),
            block_id=doc.get("block_ids", [""])[0] if doc.get("block_ids") else "",
            text_snippet=doc.get("text", "")[:300],
            score=round(score, 4),
            score_decomposition=decomp,
            metadata={
                "ordinal": doc.get("ordinal", 0),
                "entity_ids": doc.get("entity_ids", []),
            },
        )
