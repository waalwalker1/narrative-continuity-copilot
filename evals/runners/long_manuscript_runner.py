"""
Long Manuscript Stress Benchmark Runner.
Generates book-length synthetic fiction (60k-100k words) to measure latency and long-distance evidence recall.
"""

import time
from typing import Any

from narrative_copilot.ingestion.importer import ManuscriptImporter
from narrative_copilot.llm.embeddings import SentenceTransformerEmbeddingProvider
from narrative_copilot.retrieval.elasticsearch_client import ElasticsearchEngine
from narrative_copilot.retrieval.hybrid import HybridRetrievalPipeline
from narrative_copilot.schemas.retrieval import RetrievalMode, RetrievalQuery


class LongManuscriptRunner:
    def __init__(self) -> None:
        self.importer = ManuscriptImporter()
        self.embedding_provider = SentenceTransformerEmbeddingProvider()
        self.es_engine = ElasticsearchEngine()
        self.pipeline = HybridRetrievalPipeline(self.es_engine, self.embedding_provider)

    async def run_stress_test(self, target_words: int = 65000) -> dict[str, Any]:
        """
        Generate a 65k+ word manuscript with needle facts at the beginning and end,
        and benchmark indexing throughput, retrieval latency, and long-distance recall.
        """
        await self.es_engine.ensure_indices()

        # Generate synthetic book text with 30 gold needles
        chapters_md = []
        num_chapters = 35

        gold_needles: list[dict[str, Any]] = [
            {"id": f"needle_{i:02d}", "query": f"Needle Item {i} Lord Vance", "phrase": f"sacred relic number {i} preserved in vault", "chapter": i}
            for i in range(1, 31)
        ]

        for c in range(1, num_chapters + 1):
            chap_lines = [f"# Chapter {c}: Chronicle of the Long Realm Part {c}\n"]

            # Insert gold needle if matching chapter
            if c <= len(gold_needles):
                needle_info = gold_needles[c - 1]
                chap_lines.append(f"Lord Vance guarded the {needle_info['phrase']}.\n")

            # Rich filler prose (45 paragraphs per chapter = ~2,000 words per chapter)
            for p in range(45):
                chap_lines.append(
                    f"Paragraph {p}: The travelers rode steadily through the northern pines of province {c}, observing the ancient stone watchtowers. "
                    f"Scouts were dispatched to the eastern borders, river depths were sounded across the rapids, supplies of grain and salt were tallied in the logbooks, "
                    f"and horses were carefully shoed by the regimental blacksmith before the harsh winter frost settled over the mountain pass."
                )

            chapters_md.append("\n\n".join(chap_lines))

        full_text = "\n\n".join(chapters_md)
        actual_word_count = len(full_text.split())
        assert actual_word_count >= 60000, f"Manuscript must be at least 60k words, got {actual_word_count}"

        # Measure indexing
        t0 = time.perf_counter()
        units, anchors, _ = self.importer.import_text(
            content=full_text,
            format_type="markdown",
            project_id="proj_long_stress",
            revision_id="rev_long_1",
            title="Synthetic Long Fiction Benchmark",
        )

        block_units = [u for u in units if u.unit_type.value == "block"]
        texts = [b.text for b in block_units]
        vectors = await self.embedding_provider.aencode(texts)

        docs = []
        for i, b in enumerate(block_units):
            docs.append(
                {
                    "chunk_id": f"long_{b.unit_id}",
                    "project_id": "proj_long_stress",
                    "revision_id": "rev_long_1",
                    "chapter_id": b.parent_id or "",
                    "block_ids": [b.unit_id],
                    "anchor_id": anchors[i].anchor_id if i < len(anchors) else "",
                    "text": b.text,
                    "text_vector": vectors[i] if i < len(vectors) else [],
                    "ordinal": b.ordinal,
                    "point_of_view": "NARRATOR",
                }
            )
        await self.es_engine.index_chunks_bulk(docs)
        indexing_time_sec = time.perf_counter() - t0

        # Measure retrieval across all 30 needles with distance stratification
        latencies: list[float] = []
        bucket_hits: dict[str, int] = {"0_15k": 0, "15k_35k": 0, "35k_60k_plus": 0}
        bucket_totals: dict[str, int] = {"0_15k": 0, "15k_35k": 0, "35k_60k_plus": 0}
        total_hits = 0

        for needle in gold_needles:
            q_t0 = time.perf_counter()
            query = RetrievalQuery(
                query=needle["query"],
                project_id="proj_long_stress",
                revision_id="rev_long_1",
                retrieval_mode=RetrievalMode.HYBRID_RRF,
                top_k=5,
            )
            res = await self.pipeline.search(query)
            latencies.append((time.perf_counter() - q_t0) * 1000.0)

            # Determine distance bucket
            chap_num = needle["chapter"]
            if chap_num <= 7:
                bucket = "0_15k"
            elif chap_num <= 16:
                bucket = "15k_35k"
            else:
                bucket = "35k_60k_plus"

            bucket_totals[bucket] += 1

            # Check if needle retrieved
            if any(needle["phrase"] in item.text_snippet for item in res.results):
                total_hits += 1
                bucket_hits[bucket] += 1

        latencies.sort()
        p50 = latencies[len(latencies) // 2]
        p95 = latencies[int(len(latencies) * 0.95)]

        stratified_recall = {
            b: round(bucket_hits[b] / max(bucket_totals[b], 1), 4)
            for b in bucket_totals
        }

        return {
            "manuscript_word_count": actual_word_count,
            "total_blocks": len(block_units),
            "total_needles_evaluated": len(gold_needles),
            "indexing_time_seconds": round(indexing_time_sec, 2),
            "indexing_words_per_sec": round(actual_word_count / max(indexing_time_sec, 0.01), 1),
            "retrieval_latency_p50_ms": round(p50, 2),
            "retrieval_latency_p95_ms": round(p95, 2),
            "long_distance_evidence_recall": round(total_hits / max(len(gold_needles), 1), 4),
            "stratified_recall_by_distance": stratified_recall,
        }
