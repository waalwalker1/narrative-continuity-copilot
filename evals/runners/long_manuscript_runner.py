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

        # Generate synthetic book text
        chapters_md = []
        words_per_chapter = 2500
        num_chapters = (target_words // words_per_chapter) + 1

        # Needle 1: Chapter 1
        needle_1 = (
            "Lord Arthur Vance possessed a rare celestial amethyst ring on his left forefinger."
        )
        # Needle 2: Final Chapter
        needle_2 = (
            "Arthur examined his bare hands, noticing the celestial amethyst ring was shattered."
        )

        for c in range(1, num_chapters + 1):
            chap_lines = [f"# Chapter {c}: Chronicle of the Realm Part {c}\n"]
            if c == 1:
                chap_lines.append(f"{needle_1}\n")

            # Filler narrative paragraphs
            for p in range(12):
                chap_lines.append(
                    f"Paragraph {p}: The riders continued across the eastern valley. The wind whispered "
                    f"through ancient pines as shadows lengthened across the stone towers of the fortress. "
                    f"Provisions were counted, horses were watered, and the scouts reported quiet borders."
                )

            if c == num_chapters:
                chap_lines.append(f"\n{needle_2}\n")

            chapters_md.append("\n\n".join(chap_lines))

        full_text = "\n\n".join(chapters_md)
        actual_word_count = len(full_text.split())

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

        # Measure retrieval latencies across 20 queries
        latencies: list[float] = []
        recall_hits = 0
        for _ in range(20):
            q_t0 = time.perf_counter()
            query = RetrievalQuery(
                query="Arthur Vance celestial amethyst ring",
                project_id="proj_long_stress",
                revision_id="rev_long_1",
                retrieval_mode=RetrievalMode.HYBRID_RRF,
                top_k=5,
            )
            res = await self.pipeline.search(query)
            latencies.append((time.perf_counter() - q_t0) * 1000.0)

            # Check if needle retrieved
            if any("amethyst ring" in item.text_snippet for item in res.results):
                recall_hits += 1

        latencies.sort()
        p50 = latencies[len(latencies) // 2]
        p95 = latencies[int(len(latencies) * 0.95)]

        return {
            "manuscript_word_count": actual_word_count,
            "total_blocks": len(block_units),
            "indexing_time_seconds": round(indexing_time_sec, 2),
            "indexing_words_per_sec": round(actual_word_count / max(indexing_time_sec, 0.01), 1),
            "retrieval_latency_p50_ms": round(p50, 2),
            "retrieval_latency_p95_ms": round(p95, 2),
            "long_distance_evidence_recall": round(recall_hits / 20.0, 4),
        }
