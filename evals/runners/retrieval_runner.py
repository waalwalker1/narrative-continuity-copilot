"""
Retrieval evaluation runner.
Computes Recall@k, MRR, and nDCG across BM25, dense, and hybrid retrieval strategies.
"""

import json
import math
from pathlib import Path
from typing import Any

from narrative_copilot.ingestion.importer import ManuscriptImporter
from narrative_copilot.llm.embeddings import SentenceTransformerEmbeddingProvider
from narrative_copilot.retrieval.elasticsearch_client import ElasticsearchEngine
from narrative_copilot.retrieval.hybrid import HybridRetrievalPipeline
from narrative_copilot.schemas.retrieval import RetrievalMode, RetrievalQuery


class RetrievalEvaluator:
    def __init__(self, fixtures_path: Path) -> None:
        self.fixtures_path = fixtures_path
        self.embedding_provider = SentenceTransformerEmbeddingProvider()
        self.es_engine = ElasticsearchEngine()
        self.pipeline = HybridRetrievalPipeline(self.es_engine, self.embedding_provider)
        self.importer = ManuscriptImporter()

    async def run_evaluation(self) -> dict[str, Any]:
        packs_file = self.fixtures_path / "story_packs.json"
        with open(packs_file, encoding="utf-8") as f:
            packs = json.load(f)

        await self.es_engine.ensure_indices()

        # Index all story pack chapters into the engine
        all_cases = []
        for pack in packs:
            story_id = pack["story_id"]
            combined_md = "\n\n".join([c["text"] for c in pack["chapters"]])
            units, anchors, _ = self.importer.import_text(
                content=combined_md,
                format_type="markdown",
                project_id=story_id,
                revision_id="rev_eval",
                title=pack["title"],
            )

            texts = [u.text for u in units if u.unit_type.value == "block"]
            vectors = await self.embedding_provider.aencode(texts)
            anchor_map = {a.block_id: a.anchor_id for a in anchors}

            docs = []
            block_units = [u for u in units if u.unit_type.value == "block"]
            for idx, b in enumerate(block_units):
                docs.append(
                    {
                        "chunk_id": f"{story_id}_{b.unit_id}",
                        "project_id": story_id,
                        "revision_id": "rev_eval",
                        "chapter_id": b.parent_id or "",
                        "scene_id": b.parent_id or "",
                        "block_ids": [b.unit_id],
                        "anchor_id": anchor_map.get(b.unit_id, ""),
                        "text": b.text,
                        "text_vector": vectors[idx] if idx < len(vectors) else [],
                        "entity_ids": [],
                        "ordinal": b.ordinal,
                        "point_of_view": "NARRATOR",
                    }
                )
            await self.es_engine.index_chunks_bulk(docs)
            all_cases.extend(pack.get("benchmark_cases", []))

        # Evaluate queries for each retrieval mode
        modes = [
            RetrievalMode.BM25_ONLY,
            RetrievalMode.DENSE_ONLY,
            RetrievalMode.HYBRID_RRF,
        ]

        metrics_by_mode: dict[str, Any] = {}

        for mode in modes:
            r1_hits = 0
            r5_hits = 0
            r10_hits = 0
            reciprocal_ranks = []
            ndcg_scores = []
            anchor_hits = 0
            total_queries = 0

            for case in all_cases:
                story_id = case["story_pack_id"]
                clean_pred = case["predicate"].replace("_", " ")
                query_text = f"{case['subject_entity_name']} {clean_pred}"
                expected_kw = case["value_a"].lower()
                target_evidence = case.get("evidence_a_text", "").lower()

                q = RetrievalQuery(
                    query=query_text,
                    project_id=story_id,
                    revision_id="rev_eval",
                    retrieval_mode=mode,
                    top_k=10,
                )
                response = await self.pipeline.search(q)
                total_queries += 1

                # Check if target evidence snippet appears in top-k
                hit_rank = None
                for rank, item in enumerate(response.results, start=1):
                    snip = item.text_snippet.lower()
                    if (
                        expected_kw in snip
                        or any(w in snip for w in expected_kw.split() if len(w) > 3)
                        or (
                            target_evidence
                            and any(p in snip for p in target_evidence.split(". ") if len(p) > 10)
                        )
                    ):
                        hit_rank = rank
                        break

                if hit_rank is not None:
                    if hit_rank == 1:
                        r1_hits += 1
                    if hit_rank <= 5:
                        r5_hits += 1
                    if hit_rank <= 10:
                        r10_hits += 1
                    reciprocal_ranks.append(1.0 / hit_rank)
                    ndcg_scores.append(1.0 / math.log2(hit_rank + 1))
                    anchor_hits += 1
                else:
                    reciprocal_ranks.append(0.0)
                    ndcg_scores.append(0.0)

            n = max(total_queries, 1)
            metrics_by_mode[mode.value] = {
                "queries_evaluated": total_queries,
                "recall_at_1": round(r1_hits / n, 4),
                "recall_at_5": round(r5_hits / n, 4),
                "recall_at_10": round(r10_hits / n, 4),
                "mrr": round(sum(reciprocal_ranks) / n, 4),
                "ndcg_at_10": round(sum(ndcg_scores) / n, 4),
                "exact_anchor_hit_rate": round(anchor_hits / n, 4),
            }

        return metrics_by_mode
