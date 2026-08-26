"""
API Request and Response schemas.
"""

from typing import Any

from pydantic import BaseModel, Field

from narrative_copilot.schemas import (
    AuthorActionType,
    PrivacyMode,
    ProviderStatus,
)


class CreateProjectRequest(BaseModel):
    title: str
    language: str = "en"
    genre_hint: str | None = None
    privacy_mode: PrivacyMode = PrivacyMode.LOCAL_ONLY


class ImportManuscriptRequest(BaseModel):
    format: str = "markdown"  # "markdown", "plaintext", "docx"
    content_text: str | None = None
    title: str | None = None


class CreateRevisionRequest(BaseModel):
    parent_revision_id: str | None = None
    content_markdown: str


class IndexRequest(BaseModel):
    revision_id: str | None = None
    incremental: bool = False
    idempotency_key: str | None = None


class IndexStatusResponse(BaseModel):
    project_id: str
    revision_id: str
    status: str  # "IDLE", "INDEXING", "READY", "FAILED"
    progress: float = 1.0
    total_blocks: int = 0
    indexed_chunks: int = 0
    extracted_facts: int = 0
    last_error: str | None = None


class AuthorDecisionRequest(BaseModel):
    action_type: AuthorActionType
    author_notes: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)


class MergeAliasesRequest(BaseModel):
    primary_entity_id: str
    secondary_entity_ids: list[str]


class SplitEntityRequest(BaseModel):
    entity_id: str
    new_entity_canonical_name: str
    fact_ids_to_move: list[str]


class PrivacyPreviewResponse(BaseModel):
    project_id: str
    privacy_mode: PrivacyMode
    destination_provider: str
    will_transmit_raw_manuscript: bool
    spans_to_transmit: list[dict[str, Any]] = Field(default_factory=list)
    total_character_count: int = 0
    total_estimated_tokens: int = 0
    purpose: str


class ReadyResponse(BaseModel):
    status: str
    database: str
    elasticsearch: str
    embedding_provider: str
    embedding_model: str
    llm_provider: str
    schema_version: str


class ProvidersStatusResponse(BaseModel):
    providers: dict[str, ProviderStatus]
