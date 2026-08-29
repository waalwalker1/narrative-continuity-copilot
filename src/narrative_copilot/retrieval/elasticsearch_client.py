"""
Elasticsearch index management and client abstraction.
Supports both live Elasticsearch 8 instances and an in-memory test engine for isolated unit testing.
"""

import contextlib
import logging
import os
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

try:
    from elasticsearch import AsyncElasticsearch, Elasticsearch
except ImportError:
    AsyncElasticsearch = None  # type: ignore[assignment,misc]
    Elasticsearch = None  # type: ignore[assignment,misc]

CHUNKS_INDEX = "manuscript_chunks"
MEMORY_INDEX = "story_memory"

CHUNKS_MAPPING = {
    "mappings": {
        "properties": {
            "chunk_id": {"type": "keyword"},
            "project_id": {"type": "keyword"},
            "revision_id": {"type": "keyword"},
            "chapter_id": {"type": "keyword"},
            "scene_id": {"type": "keyword"},
            "block_ids": {"type": "keyword"},
            "anchor_id": {"type": "keyword"},
            "text": {"type": "text", "analyzer": "standard"},
            "text_vector": {
                "type": "dense_vector",
                "dims": 384,
                "index": True,
                "similarity": "cosine",
            },
            "entity_ids": {"type": "keyword"},
            "ordinal": {"type": "integer"},
            "point_of_view": {"type": "keyword"},
        }
    }
}

MEMORY_MAPPING = {
    "mappings": {
        "properties": {
            "doc_id": {"type": "keyword"},
            "project_id": {"type": "keyword"},
            "revision_id": {"type": "keyword"},
            "memory_type": {"type": "keyword"},  # entity, fact, relation, rule, event, thread
            "subject_entity_id": {"type": "keyword"},
            "canonical_text": {"type": "text", "analyzer": "standard"},
            "vector": {
                "type": "dense_vector",
                "dims": 384,
                "index": True,
                "similarity": "cosine",
            },
            "entity_ids": {"type": "keyword"},
            "aliases": {"type": "keyword"},
            "temporal_scope": {"type": "keyword"},
            "narrative_scope": {"type": "keyword"},
            "canonical_status": {"type": "keyword"},
            "evidence_anchor_ids": {"type": "keyword"},
        }
    }
}


class ElasticsearchEngine:
    """
    Elasticsearch retrieval client supporting hybrid BM25 and vector search.
    Includes in-memory search fallback for zero-dependency local environments.
    """

    def __init__(self, es_url: str | None = None) -> None:
        self.es_url = es_url or os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
        self._client: Elasticsearch | None = None
        self._async_client: AsyncElasticsearch | None = None
        self.use_mock = False

        # In-memory document storage for local/mock operations
        self._mock_chunks: dict[str, dict[str, Any]] = {}
        self._mock_memory: dict[str, dict[str, Any]] = {}

    def is_connected(self) -> bool:
        """Check if live Elasticsearch server is accessible."""
        if self.use_mock or Elasticsearch is None:
            return False
        if self._client is not None:
            try:
                return bool(self._client.ping())
            except Exception:
                self.use_mock = True
                return False
        try:
            self._client = Elasticsearch(self.es_url, request_timeout=0.5)
            if self._client.ping():
                return True
            self.use_mock = True
            return False
        except Exception:
            self.use_mock = True
            return False

    async def ensure_indices(self) -> None:
        """Create indices with vector mappings if they do not exist."""
        if self.is_connected() and not self.use_mock:
            try:
                client = Elasticsearch(self.es_url)
                if not client.indices.exists(index=CHUNKS_INDEX):
                    try:
                        client.indices.create(
                            index=CHUNKS_INDEX, mappings=CHUNKS_MAPPING["mappings"]
                        )
                    except Exception:
                        client.indices.create(index=CHUNKS_INDEX, body=CHUNKS_MAPPING)
                if not client.indices.exists(index=MEMORY_INDEX):
                    try:
                        client.indices.create(
                            index=MEMORY_INDEX, mappings=MEMORY_MAPPING["mappings"]
                        )
                    except Exception:
                        client.indices.create(index=MEMORY_INDEX, body=MEMORY_MAPPING)
            except Exception:
                self.use_mock = True
        else:
            self.use_mock = True

    async def index_chunk(self, doc: dict[str, Any]) -> None:
        """Index a single manuscript chunk document."""
        chunk_id = doc["chunk_id"]
        self._mock_chunks[chunk_id] = doc
        if self.is_connected() and not self.use_mock:
            try:
                client = Elasticsearch(self.es_url)
                doc_copy = dict(doc)
                if not doc_copy.get("text_vector") or len(doc_copy.get("text_vector", [])) != 384:
                    doc_copy["text_vector"] = [0.0] * 384
                client.index(index=CHUNKS_INDEX, id=chunk_id, document=doc_copy, refresh=True)
            except Exception as exc:
                logger.debug("Failed chunk indexing: %s", exc)

    async def index_chunks_bulk(self, docs: list[dict[str, Any]]) -> int:
        """Bulk index manuscript chunk documents."""
        if not docs:
            return 0
        for d in docs:
            self._mock_chunks[d["chunk_id"]] = d
        if not self.use_mock and self.is_connected():
            try:
                client = Elasticsearch(self.es_url)
                for d in docs:
                    doc_copy = dict(d)
                    if (
                        not doc_copy.get("text_vector")
                        or len(doc_copy.get("text_vector", [])) != 384
                    ):
                        doc_copy["text_vector"] = [0.0] * 384
                    client.index(index=CHUNKS_INDEX, id=d["chunk_id"], document=doc_copy)
                client.indices.refresh(index=CHUNKS_INDEX)
            except Exception as exc:
                logger.debug("Failed bulk chunk indexing: %s", exc)
        return len(docs)

    async def index_memory_doc(self, doc: dict[str, Any]) -> None:
        """Index a single story memory document."""
        doc_id = doc["doc_id"]
        self._mock_memory[doc_id] = doc
        if not self.use_mock and self.is_connected():
            try:
                client = Elasticsearch(self.es_url)
                doc_copy = dict(doc)
                if not doc_copy.get("vector") or len(doc_copy.get("vector", [])) != 384:
                    doc_copy["vector"] = [0.0] * 384
                client.index(index=MEMORY_INDEX, id=doc_id, document=doc_copy)
                client.indices.refresh(index=MEMORY_INDEX)
            except Exception as exc:
                logger.debug("Failed memory doc indexing: %s", exc)

    async def index_memory_bulk(self, docs: list[dict[str, Any]]) -> int:
        """Bulk index story memory documents."""
        if not docs:
            return 0
        for d in docs:
            self._mock_memory[d["doc_id"]] = d
        if not self.use_mock and self.is_connected():
            try:
                client = Elasticsearch(self.es_url)
                for d in docs:
                    doc_copy = dict(d)
                    if not doc_copy.get("vector") or len(doc_copy.get("vector", [])) != 384:
                        doc_copy["vector"] = [0.0] * 384
                    client.index(index=MEMORY_INDEX, id=d["doc_id"], document=doc_copy)
                client.indices.refresh(index=MEMORY_INDEX)
            except Exception as exc:
                logger.debug("Failed bulk memory indexing: %s", exc)
        return len(docs)

    async def delete_chunks_by_ids(self, project_id: str, chunk_ids: list[str]) -> None:
        """Delete specific chunk documents by ID."""
        if not chunk_ids:
            return
        if self.is_connected() and not self.use_mock:
            client = Elasticsearch(self.es_url)
            query = {
                "bool": {
                    "must": [
                        {"term": {"project_id": project_id}},
                        {"terms": {"chunk_id": chunk_ids}},
                    ]
                }
            }
            with contextlib.suppress(Exception):
                client.delete_by_query(index=CHUNKS_INDEX, body={"query": query})
        else:
            to_del = [
                k
                for k, v in self._mock_chunks.items()
                if v.get("project_id") == project_id and v.get("chunk_id") in chunk_ids
            ]
            for k in to_del:
                self._mock_chunks.pop(k, None)

    async def delete_memory_by_ids(self, project_id: str, doc_ids: list[str]) -> None:
        """Delete specific memory documents by ID."""
        if not doc_ids:
            return
        if self.is_connected() and not self.use_mock:
            client = Elasticsearch(self.es_url)
            query = {
                "bool": {
                    "must": [
                        {"term": {"project_id": project_id}},
                        {"terms": {"doc_id": doc_ids}},
                    ]
                }
            }
            with contextlib.suppress(Exception):
                client.delete_by_query(index=MEMORY_INDEX, body={"query": query})
        else:
            to_del = [
                k
                for k, v in self._mock_memory.items()
                if v.get("project_id") == project_id and v.get("doc_id") in doc_ids
            ]
            for k in to_del:
                self._mock_memory.pop(k, None)

    async def delete_memory_by_anchors(self, project_id: str, anchor_ids: list[str]) -> None:
        """Delete memory documents referencing invalid/updated anchors."""
        if not anchor_ids:
            return
        if self.is_connected() and not self.use_mock:
            client = Elasticsearch(self.es_url)
            query = {
                "bool": {
                    "must": [
                        {"term": {"project_id": project_id}},
                        {"terms": {"evidence_anchor_ids": anchor_ids}},
                    ]
                }
            }
            client.delete_by_query(index=MEMORY_INDEX, body={"query": query})
        else:
            to_del = [
                k
                for k, v in self._mock_memory.items()
                if v.get("project_id") == project_id
                and any(a in v.get("evidence_anchor_ids", []) for a in anchor_ids)
            ]
            for k in to_del:
                self._mock_memory.pop(k, None)

    async def search_memory(
        self,
        query: str,
        project_id: str,
        revision_id: str | None = None,
        memory_types: list[str] | None = None,
        top_k: int = 10,
    ) -> list[tuple[dict[str, Any], float]]:
        """Search story memory index for relevant facts, rules, events, relations."""
        if self.is_connected() and not self.use_mock:
            try:
                client = Elasticsearch(self.es_url)
                must_clauses: list[dict[str, Any]] = [
                    {"match": {"canonical_text": query}},
                    {"term": {"project_id": project_id}},
                ]
                if revision_id:
                    must_clauses.append({"term": {"revision_id": revision_id}})
                if memory_types:
                    must_clauses.append({"terms": {"memory_type": memory_types}})

                res = client.search(
                    index=MEMORY_INDEX,
                    query={"bool": {"must": must_clauses}},
                    size=top_k,
                )
                return [(hit["_source"], float(hit["_score"])) for hit in res["hits"]["hits"]]
            except Exception as exc:
                logger.warning(
                    "Live Elasticsearch search_memory failed: %s, using in-memory fallback", exc
                )

        # In-memory mock search
        results: list[tuple[dict[str, Any], float]] = []
        tokens = query.lower().split()
        for doc in self._mock_memory.values():
            if doc.get("project_id") != project_id:
                continue
            if revision_id and doc.get("revision_id") != revision_id:
                continue
            if memory_types and doc.get("memory_type") not in memory_types:
                continue

            text_lower = doc.get("canonical_text", "").lower()
            score = 0.0
            for t in tokens:
                count = text_lower.count(t)
                if count > 0:
                    score += count * 2.0
            if score > 0:
                results.append((doc, score))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    async def delete_revision_documents(self, project_id: str, revision_id: str) -> None:
        """Remove indexed documents for a specific revision."""
        if self.is_connected() and not self.use_mock:
            await self.ensure_indices()
            with contextlib.suppress(Exception):
                client = Elasticsearch(self.es_url)
                query = {
                    "bool": {
                        "must": [
                            {"term": {"project_id": project_id}},
                            {"term": {"revision_id": revision_id}},
                        ]
                    }
                }
                with contextlib.suppress(Exception):
                    client.delete_by_query(index=CHUNKS_INDEX, body={"query": query})
                with contextlib.suppress(Exception):
                    client.delete_by_query(index=MEMORY_INDEX, body={"query": query})
        else:
            self._mock_chunks = {
                k: v
                for k, v in self._mock_chunks.items()
                if not (v.get("project_id") == project_id and v.get("revision_id") == revision_id)
            }
            self._mock_memory = {
                k: v
                for k, v in self._mock_memory.items()
                if not (v.get("project_id") == project_id and v.get("revision_id") == revision_id)
            }

    def get_revision_chunk_vectors(
        self, project_id: str, revision_id: str
    ) -> dict[str, list[float]]:
        """Retrieve cached text_vector embeddings for a specific revision's blocks."""
        vectors: dict[str, list[float]] = {}
        for doc in self._mock_chunks.values():
            if doc.get("project_id") == project_id and doc.get("revision_id") == revision_id:
                b_ids = doc.get("block_ids", [])
                vec = doc.get("text_vector", [])
                if b_ids and vec:
                    vectors[b_ids[0]] = vec
        if vectors:
            return vectors

        if not self.use_mock and self.is_connected():
            try:
                client = Elasticsearch(self.es_url)
                query = {
                    "bool": {
                        "must": [
                            {"term": {"project_id": project_id}},
                            {"term": {"revision_id": revision_id}},
                        ]
                    }
                }
                res = client.search(
                    index=CHUNKS_INDEX,
                    body={"query": query, "size": 10000, "_source": ["block_ids", "text_vector"]},
                )
                for hit in res.get("hits", {}).get("hits", []):
                    src = hit.get("_source", {})
                    b_ids = src.get("block_ids", [])
                    vec = src.get("text_vector", [])
                    if b_ids and vec:
                        vectors[b_ids[0]] = vec
            except Exception as exc:
                logger.debug("Failed to retrieve revision chunk vectors from ES: %s", exc)
        return vectors

    async def clear_all_indices(self) -> None:
        """Remove all indexed chunk and memory documents across all projects."""
        if self.is_connected() and not self.use_mock:
            await self.ensure_indices()
            with contextlib.suppress(Exception):
                client = Elasticsearch(self.es_url)
                client.delete_by_query(index=CHUNKS_INDEX, body={"query": {"match_all": {}}})
                client.delete_by_query(index=MEMORY_INDEX, body={"query": {"match_all": {}}})
        self._mock_chunks.clear()
        self._mock_memory.clear()

    def bm25_search_chunks(
        self,
        query: str,
        project_id: str,
        revision_id: str | None = None,
        entity_ids: list[str] | None = None,
        top_k: int = 10,
    ) -> list[tuple[dict[str, Any], float]]:
        """Lexical BM25 search over manuscript chunks."""
        if self.is_connected() and not self.use_mock:
            try:
                client = Elasticsearch(self.es_url)
                must_clauses: list[dict[str, Any]] = [
                    {"match": {"text": query}},
                    {"term": {"project_id": project_id}},
                ]
                if revision_id:
                    must_clauses.append({"term": {"revision_id": revision_id}})
                if entity_ids:
                    must_clauses.append({"terms": {"entity_ids": entity_ids}})

                res = client.search(
                    index=CHUNKS_INDEX,
                    body={"query": {"bool": {"must": must_clauses}}, "size": top_k},
                )
                return [(hit["_source"], float(hit["_score"])) for hit in res["hits"]["hits"]]
            except Exception as exc:
                logger.debug("Elasticsearch BM25 search failed: %s", exc)

        # In-memory BM25 simulation
        results: list[tuple[dict[str, Any], float]] = []
        tokens = query.lower().split()
        for doc in self._mock_chunks.values():
            if doc.get("project_id") != project_id:
                continue
            if revision_id and doc.get("revision_id") != revision_id:
                continue
            if entity_ids:
                doc_entities = doc.get("entity_ids", [])
                if not any(e in doc_entities for e in entity_ids):
                    continue

            text_lower = doc.get("text", "").lower()
            score = 0.0
            for t in tokens:
                count = text_lower.count(t)
                if count > 0:
                    score += count * 1.5
            if score > 0:
                results.append((doc, score))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def vector_search_chunks(
        self,
        query_vector: list[float],
        project_id: str,
        revision_id: str | None = None,
        top_k: int = 10,
    ) -> list[tuple[dict[str, Any], float]]:
        """Dense vector search using cosine similarity."""
        if self.is_connected() and not self.use_mock:
            try:
                client = Elasticsearch(self.es_url)
                filter_clauses: list[dict[str, Any]] = [{"term": {"project_id": project_id}}]
                if revision_id:
                    filter_clauses.append({"term": {"revision_id": revision_id}})

                res = client.search(
                    index=CHUNKS_INDEX,
                    knn={
                        "field": "text_vector",
                        "query_vector": query_vector,
                        "k": top_k,
                        "num_candidates": max(top_k * 5, 50),
                        "filter": filter_clauses,
                    },
                )
                return [(hit["_source"], float(hit["_score"])) for hit in res["hits"]["hits"]]
            except Exception as exc:
                logger.debug("Elasticsearch vector search failed: %s", exc)

        # In-memory cosine similarity
        q_vec = np.array(query_vector, dtype=float)
        q_norm = np.linalg.norm(q_vec)
        results: list[tuple[dict[str, Any], float]] = []

        for doc in self._mock_chunks.values():
            if doc.get("project_id") != project_id:
                continue
            if revision_id and doc.get("revision_id") != revision_id:
                continue

            doc_vec_raw = doc.get("text_vector")
            if not doc_vec_raw:
                continue
            d_vec = np.array(doc_vec_raw, dtype=float)
            d_norm = np.linalg.norm(d_vec)
            if q_norm > 0 and d_norm > 0:
                sim = float(np.dot(q_vec, d_vec) / (q_norm * d_norm))
                results.append((doc, sim))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
