"""
FastAPI application for Narrative Continuity Copilot.
Exposes REST endpoints for manuscript management, story memory, hybrid retrieval, and continuity review.
"""

from contextlib import asynccontextmanager
from typing import Any
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy.ext.asyncio import AsyncSession

from narrative_copilot.anchors.reanchoring import ReanchoringEngine
from narrative_copilot.continuity.engine import ContinuityReasoningEngine
from narrative_copilot.ingestion.importer import IngestionError, ManuscriptImporter
from narrative_copilot.llm.deterministic_fixture import DeterministicFixtureLLMProvider
from narrative_copilot.llm.embeddings import (
    SentenceTransformerEmbeddingProvider,
)
from narrative_copilot.memory.extractor import StoryMemoryExtractor
from narrative_copilot.observability.logging import log_privacy_safe
from narrative_copilot.persistence.db import Database
from narrative_copilot.persistence.repository import Repository
from narrative_copilot.retrieval.elasticsearch_client import ElasticsearchEngine
from narrative_copilot.retrieval.hybrid import HybridRetrievalPipeline
from narrative_copilot.schemas import (
    AuthorDecision,
    ContinuityAlert,
    ManuscriptProject,
    ManuscriptRevision,
    ProviderStatus,
    SourceAnchor,
    StoryMemory,
    StructuralUnit,
    UnitType,
)
from narrative_copilot.schemas.api import (
    AuthorDecisionRequest,
    CreateProjectRequest,
    CreateRevisionRequest,
    ImportManuscriptRequest,
    IndexRequest,
    IndexStatusResponse,
    PrivacyPreviewResponse,
    ProvidersStatusResponse,
    ReadyResponse,
)
from narrative_copilot.schemas.errors import ApiErrorDetail, ApiErrorResponse, ErrorCode
from narrative_copilot.schemas.retrieval import (
    RetrievalQuery,
    RetrievalResponse,
)
from narrative_copilot.structure.parser import compute_text_hash

# Global singletons
db = Database()
es_engine = ElasticsearchEngine()
embedding_provider = SentenceTransformerEmbeddingProvider()
llm_provider = DeterministicFixtureLLMProvider()
hybrid_retrieval = HybridRetrievalPipeline(es_engine, embedding_provider)
importer = ManuscriptImporter()
reanchoring_engine = ReanchoringEngine()
story_memory_extractor = StoryMemoryExtractor(llm_provider)
continuity_engine = ContinuityReasoningEngine(llm_provider)


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
    await db.init_db()
    await es_engine.ensure_indices()
    log_privacy_safe("application_startup_complete")
    yield


app = FastAPI(
    title="Narrative Continuity Copilot API",
    description="Evidence-grounded story memory and narrative continuity analysis.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def get_repo(session: AsyncSession = Depends(db.get_session)) -> Repository:
    return Repository(session)


@app.exception_handler(IngestionError)
async def ingestion_exception_handler(request: Request, exc: IngestionError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ApiErrorResponse(
            error=ApiErrorDetail(code=exc.code, message=exc.message)
        ).model_dump(),
    )


# --- System Probes & Metrics ---
@app.get("/health")
async def health_probe() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
async def readiness_probe() -> ReadyResponse:
    es_status = "connected" if es_engine.is_connected() else "in_memory_fallback"
    return ReadyResponse(
        status="ready",
        database="connected",
        elasticsearch=es_status,
        embedding_provider="sentence-transformers",
        embedding_model=embedding_provider.model_name,
        llm_provider="deterministic-fixture",
        schema_version="0.1.0",
    )


@app.get("/metrics")
async def prometheus_metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/api/v1/system/providers")
async def get_providers_status() -> ProvidersStatusResponse:
    return ProvidersStatusResponse(
        providers={
            "deterministic_fixture": ProviderStatus.IMPLEMENTED_AND_TESTED,
            "sentence_transformers": ProviderStatus.IMPLEMENTED_AND_TESTED,
            "vertex_ai": ProviderStatus.CONTRACT_TESTED,
            "elasticsearch": ProviderStatus.IMPLEMENTED_AND_TESTED,
        }
    )


# --- Projects & Structure ---
@app.post("/api/v1/projects", status_code=status.HTTP_201_CREATED)
async def create_project(
    req: CreateProjectRequest, repo: Repository = Depends(get_repo)
) -> ManuscriptProject:
    project = ManuscriptProject(
        title=req.title,
        language=req.language,
        genre_hint=req.genre_hint,
        privacy_mode=req.privacy_mode,
    )
    return await repo.create_project(project)


@app.get("/api/v1/projects")
async def list_projects(repo: Repository = Depends(get_repo)) -> list[ManuscriptProject]:
    return await repo.list_projects()


@app.get("/api/v1/projects/{project_id}")
async def get_project(project_id: str, repo: Repository = Depends(get_repo)) -> ManuscriptProject:
    project = await repo.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ApiErrorDetail(
                code=ErrorCode.PROJECT_NOT_FOUND, message="Project not found"
            ).model_dump(),
        )
    return project


@app.post("/api/v1/projects/{project_id}/import")
async def import_manuscript(
    project_id: str,
    req: ImportManuscriptRequest,
    repo: Repository = Depends(get_repo),
) -> dict[str, Any]:
    project = await repo.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ApiErrorDetail(
                code=ErrorCode.PROJECT_NOT_FOUND, message="Project not found"
            ).model_dump(),
        )

    content = req.content_text or ""
    revision_id = str(uuid4())
    units, anchors, md_text = importer.import_text(
        content=content,
        format_type=req.format,
        project_id=project_id,
        revision_id=revision_id,
        title=req.title or project.title,
    )

    revision = ManuscriptRevision(
        revision_id=revision_id,
        project_id=project_id,
        source_hash=compute_text_hash(md_text),
        word_count=len(md_text.split()),
        structure_version=1,
    )

    await repo.create_revision(revision, raw_markdown=md_text)
    await repo.save_structural_units(units)
    await repo.save_anchors(anchors)
    await repo.update_project_active_revision(project_id, revision_id)

    log_privacy_safe(
        "manuscript_imported",
        {"project_id": project_id, "revision_id": revision_id, "units_count": len(units)},
    )

    return {
        "project_id": project_id,
        "revision_id": revision_id,
        "units_count": len(units),
        "anchors_count": len(anchors),
    }


@app.get("/api/v1/projects/{project_id}/structure")
async def get_manuscript_structure(
    project_id: str,
    revision_id: str | None = None,
    repo: Repository = Depends(get_repo),
) -> list[StructuralUnit]:
    project = await repo.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    target_rev = revision_id or project.active_revision_id
    if not target_rev:
        return []

    return await repo.get_structural_units(target_rev)


@app.post("/api/v1/projects/{project_id}/revisions")
async def create_revision(
    project_id: str,
    req: CreateRevisionRequest,
    repo: Repository = Depends(get_repo),
) -> dict[str, Any]:
    project = await repo.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    new_rev_id = str(uuid4())
    parent_rev_id = req.parent_revision_id or project.active_revision_id

    # Retrieve existing anchors for re-anchoring
    existing_anchors: list[SourceAnchor] = []
    if parent_rev_id:
        existing_anchors = await repo.get_anchors(parent_rev_id)

    units, anchors, md_text = importer.import_text(
        content=req.content_markdown,
        format_type="markdown",
        project_id=project_id,
        revision_id=new_rev_id,
        title=project.title,
    )

    revision = ManuscriptRevision(
        revision_id=new_rev_id,
        project_id=project_id,
        parent_revision_id=parent_rev_id,
        source_hash=compute_text_hash(md_text),
        word_count=len(md_text.split()),
        structure_version=1,
    )

    await repo.create_revision(revision, raw_markdown=md_text)
    await repo.save_structural_units(units)
    await repo.save_anchors(anchors)
    await repo.update_project_active_revision(project_id, new_rev_id)

    # Re-anchor existing facts
    reanchor_results = reanchoring_engine.reanchor_all(
        anchors=existing_anchors,
        target_revision_id=new_rev_id,
        target_blocks=units,
    )

    log_privacy_safe(
        "revision_created",
        {
            "project_id": project_id,
            "revision_id": new_rev_id,
            "reanchors_count": len(reanchor_results),
        },
    )

    return {
        "project_id": project_id,
        "revision_id": new_rev_id,
        "reanchors_evaluated": len(reanchor_results),
    }


@app.post("/api/v1/projects/{project_id}/revisions/from-edits")
async def create_revision_from_scoped_edits(
    project_id: str,
    req: ScopedEditRequest,
    repo: Repository = Depends(get_repo),
) -> dict[str, Any]:
    """
    Safely construct a new project revision from scoped chapter editing,
    preserving all untouched chapters and generating re-anchored citations.
    """
    project = await repo.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    base_rev_id = req.base_revision_id or project.active_revision_id
    if not base_rev_id:
        raise HTTPException(status_code=400, detail="No base revision found")

    base_units = await repo.get_structural_units(base_rev_id)
    base_anchors = await repo.get_anchors(base_rev_id)

    # Reconstruct the manuscript by replacing the target chapter content
    chapter_units = [u for u in base_units if u.unit_type == UnitType.CHAPTER]
    new_chapter_texts: list[str] = []

    for chap in chapter_units:
        if chap.unit_id == req.chapter_id or chap.title == req.chapter_id:
            new_chapter_texts.append(req.chapter_content_markdown.strip())
        else:
            # Gather blocks for this chapter
            chap_blocks = [
                u.text
                for u in base_units
                if u.unit_type == UnitType.BLOCK and u.parent_id == chap.unit_id
            ]
            chap_body = "\n\n".join(chap_blocks)
            new_chapter_texts.append(f"# {chap.title}\n\n{chap_body}".strip())

    reconstructed_markdown = "\n\n".join(new_chapter_texts)

    # Ingest and create new revision
    new_rev_id = str(uuid4())
    units, anchors, rev = importer.import_text(
        content=reconstructed_markdown,
        format_type="markdown",
        project_id=project_id,
        revision_id=new_rev_id,
        title=project.title,
    )
    rev.parent_revision_id = base_rev_id

    await repo.save_revision(rev)
    await repo.save_structural_units(units)
    await repo.save_anchors(anchors)
    await repo.update_project_active_revision(project_id, new_rev_id)

    # Execute re-anchoring from base revision
    reanchoring_engine = ReanchoringEngine()
    reanchor_results = []
    for anc in base_anchors:
        res = reanchoring_engine.reanchor(anc, new_rev_id, units)
        reanchor_results.append(res)

    return {
        "project_id": project_id,
        "revision_id": new_rev_id,
        "base_revision_id": base_rev_id,
        "word_count": rev.word_count,
        "reanchors_evaluated": len(reanchor_results),
    }


# --- Indexing & Search ---
@app.post("/api/v1/projects/{project_id}/index")
async def index_project(
    project_id: str,
    req: IndexRequest,
    repo: Repository = Depends(get_repo),
) -> IndexStatusResponse:
    project = await repo.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    target_rev = req.revision_id or project.active_revision_id
    if not target_rev:
        raise HTTPException(status_code=400, detail="No active revision to index.")

    units = await repo.get_structural_units(target_rev)
    anchors = await repo.get_anchors(target_rev)
    block_units = [u for u in units if u.unit_type == UnitType.BLOCK]

    # Delete old index documents for this revision to maintain idempotency
    await es_engine.delete_revision_documents(project_id, target_rev)

    # 1. Compute embeddings and index chunks into Elasticsearch
    texts = [b.text for b in block_units]
    vectors = await embedding_provider.aencode(texts)

    anchor_map = {a.block_id: a.anchor_id for a in anchors}
    docs_to_index: list[dict[str, Any]] = []

    for i, block in enumerate(block_units):
        docs_to_index.append(
            {
                "chunk_id": f"{project_id}_{target_rev}_{block.unit_id}",
                "project_id": project_id,
                "revision_id": target_rev,
                "chapter_id": block.parent_id or "",
                "scene_id": block.parent_id or "",
                "block_ids": [block.unit_id],
                "anchor_id": anchor_map.get(block.unit_id, ""),
                "text": block.text,
                "text_vector": vectors[i] if i < len(vectors) else [],
                "entity_ids": [],
                "ordinal": block.ordinal,
                "point_of_view": "NARRATOR",
            }
        )

    await es_engine.index_chunks_bulk(docs_to_index)

    # 2. Extract story memory
    memory = await story_memory_extractor.extract_memory(
        project_id=project_id,
        revision_id=target_rev,
        units=units,
        anchors=anchors,
    )

    # Persist all memory types
    await repo.save_entities(memory.entities)
    await repo.save_facts(memory.facts)
    await repo.save_relations(memory.relations)
    await repo.save_timeline_events(memory.timeline_events)
    await repo.save_world_rules(memory.world_rules)
    await repo.save_story_threads(memory.story_threads)

    # Index structured memory documents into Elasticsearch MEMORY_INDEX
    memory_docs: list[dict[str, Any]] = []
    for f in memory.facts:
        memory_docs.append(
            {
                "doc_id": f.fact_id,
                "project_id": project_id,
                "revision_id": target_rev,
                "memory_type": "fact",
                "subject_entity_id": f.subject_entity_id,
                "canonical_text": f"{f.predicate}: {f.value or f.normalized_value}",
                "vector": [],
                "entity_ids": [f.subject_entity_id] + ([f.object_entity_id] if f.object_entity_id else []),
                "aliases": [],
                "temporal_scope": f.temporal_scope,
                "narrative_scope": f.narrative_scope.value,
                "canonical_status": f.canonical_status.value,
                "evidence_anchor_ids": f.evidence_anchor_ids,
            }
        )
    for r in memory.relations:
        memory_docs.append(
            {
                "doc_id": r.relation_id,
                "project_id": project_id,
                "revision_id": target_rev,
                "memory_type": "relation",
                "subject_entity_id": r.subject_entity_id,
                "canonical_text": f"{r.relation_type} -> {r.object_entity_id}",
                "vector": [],
                "entity_ids": [r.subject_entity_id, r.object_entity_id],
                "aliases": [],
                "temporal_scope": r.temporal_validity,
                "narrative_scope": r.narrative_scope.value,
                "canonical_status": r.canonical_status.value,
                "evidence_anchor_ids": r.evidence_anchor_ids,
            }
        )
    for w in memory.world_rules:
        memory_docs.append(
            {
                "doc_id": w.rule_id,
                "project_id": project_id,
                "revision_id": target_rev,
                "memory_type": "rule",
                "subject_entity_id": "world_rule",
                "canonical_text": w.rule_statement,
                "vector": [],
                "entity_ids": [],
                "aliases": [],
                "temporal_scope": "GLOBAL",
                "narrative_scope": "GLOBAL_CANON",
                "canonical_status": w.canonical_status.value,
                "evidence_anchor_ids": w.evidence_anchor_ids,
            }
        )
    await es_engine.index_memory_bulk(memory_docs)

    log_privacy_safe(
        "indexing_completed",
        {
            "project_id": project_id,
            "revision_id": target_rev,
            "chunks_indexed": len(docs_to_index),
            "facts_extracted": len(memory.facts),
            "relations_extracted": len(memory.relations),
            "timeline_events_extracted": len(memory.timeline_events),
            "world_rules_extracted": len(memory.world_rules),
            "story_threads_extracted": len(memory.story_threads),
        },
    )

    return IndexStatusResponse(
        project_id=project_id,
        revision_id=target_rev,
        status="READY",
        progress=1.0,
        total_blocks=len(block_units),
        indexed_chunks=len(docs_to_index),
        extracted_facts=len(memory.facts),
    )


@app.post("/api/v1/projects/{project_id}/retrieve")
async def retrieve_evidence(
    project_id: str,
    query: RetrievalQuery,
) -> RetrievalResponse:
    query.project_id = project_id
    return await hybrid_retrieval.search(query)


# --- Memory & Continuity ---
@app.get("/api/v1/projects/{project_id}/memory")
async def get_story_memory(
    project_id: str,
    revision_id: str | None = None,
    repo: Repository = Depends(get_repo),
) -> StoryMemory:
    project = await repo.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    target_rev = revision_id or project.active_revision_id or ""
    entities = await repo.get_entities(project_id)
    facts = await repo.get_facts(target_rev)
    relations = await repo.get_relations(target_rev)
    timeline_events = await repo.get_timeline_events(target_rev)
    world_rules = await repo.get_world_rules(target_rev)
    story_threads = await repo.get_story_threads(target_rev)

    return StoryMemory(
        project_id=project_id,
        revision_id=target_rev,
        entities=entities,
        facts=facts,
        relations=relations,
        timeline_events=timeline_events,
        world_rules=world_rules,
        story_threads=story_threads,
    )


@app.post("/api/v1/projects/{project_id}/continuity/check")
async def run_continuity_check(
    project_id: str,
    repo: Repository = Depends(get_repo),
) -> list[ContinuityAlert]:
    project = await repo.get_project(project_id)
    if not project or not project.active_revision_id:
        raise HTTPException(status_code=404, detail="Active revision not found")

    target_rev = project.active_revision_id
    units = await repo.get_structural_units(target_rev)
    anchors = await repo.get_anchors(target_rev)
    entities = await repo.get_entities(project_id)
    facts = await repo.get_facts(target_rev)
    relations = await repo.get_relations(target_rev)
    timeline_events = await repo.get_timeline_events(target_rev)
    world_rules = await repo.get_world_rules(target_rev)
    story_threads = await repo.get_story_threads(target_rev)

    # Get suppressed alert keys from prior author decisions
    existing_alerts = await repo.get_alerts(project_id)
    suppressed_keys = {
        f"{a.evidence_a.anchor_id}:{a.evidence_b.anchor_id}"
        for a in existing_alerts
        if a.suppressed
    } | {
        f"{a.evidence_b.anchor_id}:{a.evidence_a.anchor_id}"
        for a in existing_alerts
        if a.suppressed
    }

    memory = StoryMemory(
        project_id=project_id,
        revision_id=target_rev,
        entities=entities,
        facts=facts,
        relations=relations,
        timeline_events=timeline_events,
        world_rules=world_rules,
        story_threads=story_threads,
    )

    alerts = await continuity_engine.review_continuity(
        memory=memory,
        anchors=anchors,
        units=units,
        suppressed_alert_keys=suppressed_keys,
    )
    await repo.save_alerts(alerts)

    log_privacy_safe(
        "continuity_check_completed", {"project_id": project_id, "alerts_count": len(alerts)}
    )
    return alerts


@app.get("/api/v1/projects/{project_id}/continuity/alerts")
async def get_continuity_alerts(
    project_id: str,
    repo: Repository = Depends(get_repo),
) -> list[ContinuityAlert]:
    return await repo.get_alerts(project_id)


@app.post("/api/v1/projects/{project_id}/continuity/alerts/{alert_id}/decision")
async def apply_author_decision(
    project_id: str,
    alert_id: str,
    req: AuthorDecisionRequest,
    repo: Repository = Depends(get_repo),
) -> dict[str, str]:
    decision = AuthorDecision(
        project_id=project_id,
        alert_id=alert_id,
        action_type=req.action_type,
        author_notes=req.author_notes,
        parameters=req.parameters,
    )
    await repo.record_author_decision(decision)
    log_privacy_safe(
        "author_decision_recorded",
        {"project_id": project_id, "alert_id": alert_id, "action": req.action_type.value},
    )
    return {"status": "success", "decision_id": decision.decision_id}


@app.get("/api/v1/projects/{project_id}/privacy/preview")
async def get_privacy_preview(
    project_id: str,
    repo: Repository = Depends(get_repo),
) -> PrivacyPreviewResponse:
    project = await repo.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return PrivacyPreviewResponse(
        project_id=project_id,
        privacy_mode=project.privacy_mode,
        destination_provider="Local SentenceTransformers / Deterministic Fixtures",
        will_transmit_raw_manuscript=False,
        spans_to_transmit=[],
        total_character_count=0,
        total_estimated_tokens=0,
        purpose="Evidence-grounded local continuity verification. Zero manuscript text transmitted to external cloud.",
    )
