"""
SQLAlchemy database models for Narrative Continuity Copilot.
"""

from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ProjectModel(Base):
    __tablename__ = "projects"

    project_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    active_revision_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    language: Mapped[str] = mapped_column(String(16), default="en")
    genre_hint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    privacy_mode: Mapped[str] = mapped_column(String(32), default="LOCAL_ONLY")


class RevisionModel(Base):
    __tablename__ = "revisions"

    revision_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("projects.project_id"), nullable=False
    )
    parent_revision_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    source_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    structure_version: Mapped[int] = mapped_column(Integer, default=1)
    raw_markdown: Mapped[str] = mapped_column(Text, default="")


class StructuralUnitModel(Base):
    __tablename__ = "structural_units"

    unit_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    revision_id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    project_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    unit_type: Mapped[str] = mapped_column(String(32), nullable=False)
    parent_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ordinal: Mapped[int] = mapped_column(Integer, default=0)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    text: Mapped[str] = mapped_column(Text, default="")
    word_count: Mapped[int] = mapped_column(Integer, default=0)


class SourceAnchorModel(Base):
    __tablename__ = "source_anchors"

    anchor_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    revision_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    chapter_id: Mapped[str] = mapped_column(String(64), nullable=False)
    scene_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    block_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    char_start: Mapped[int] = mapped_column(Integer, default=0)
    char_end: Mapped[int] = mapped_column(Integer, default=0)
    text_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    normalized_quote: Mapped[str] = mapped_column(Text, default="")
    previous_block_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    next_block_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)


class EntityModel(Base):
    __tablename__ = "entities"

    entity_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    canonical_name: Mapped[str] = mapped_column(String(255), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(32), default="character")
    aliases_json: Mapped[str] = mapped_column(Text, default="[]")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    canonical_status: Mapped[str] = mapped_column(String(32), default="PROPOSED")
    evidence_anchor_ids_json: Mapped[str] = mapped_column(Text, default="[]")


class FactModel(Base):
    __tablename__ = "facts"

    fact_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    revision_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    subject_entity_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    predicate: Mapped[str] = mapped_column(String(128), nullable=False)
    object_entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    normalized_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    temporal_scope: Mapped[str] = mapped_column(String(64), default="GLOBAL")
    narrative_scope: Mapped[str] = mapped_column(String(64), default="GLOBAL_CANON")
    epistemic_status: Mapped[str] = mapped_column(String(64), default="OBSERVED")
    canonical_status: Mapped[str] = mapped_column(String(64), default="PROPOSED")
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    evidence_anchor_ids_json: Mapped[str] = mapped_column(Text, default="[]")


class ContinuityAlertModel(Base):
    __tablename__ = "continuity_alerts"

    alert_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    revision_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    conflict_class: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.95)
    confidence_category: Mapped[str] = mapped_column(String(32), default="HIGH")
    explanation: Mapped[str] = mapped_column(Text, default="")
    alternate_interpretations_json: Mapped[str] = mapped_column(Text, default="[]")
    evidence_a_json: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_b_json: Mapped[str] = mapped_column(Text, nullable=False)
    chapter_location: Mapped[str | None] = mapped_column(String(128), nullable=True)
    requires_author_review: Mapped[bool] = mapped_column(Boolean, default=True)
    canonical_status: Mapped[str] = mapped_column(String(32), default="PROPOSED")
    suppressed: Mapped[bool] = mapped_column(Boolean, default=False)
    decision_id: Mapped[str | None] = mapped_column(String(64), nullable=True)


class AuthorDecisionModel(Base):
    __tablename__ = "author_decisions"

    decision_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    alert_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)
    author_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    applied_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    parameters_json: Mapped[str] = mapped_column(Text, default="{}")


class IndexJobModel(Base):
    __tablename__ = "index_jobs"

    job_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    revision_id: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="IDLE")  # IDLE, INDEXING, READY, FAILED
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    total_blocks: Mapped[int] = mapped_column(Integer, default=0)
    indexed_chunks: Mapped[int] = mapped_column(Integer, default=0)
    extracted_facts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class RelationModel(Base):
    __tablename__ = "relations"

    relation_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    revision_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    subject_entity_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    relation_type: Mapped[str] = mapped_column(String(128), nullable=False)
    object_entity_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    temporal_validity: Mapped[str] = mapped_column(String(64), default="GLOBAL")
    narrative_scope: Mapped[str] = mapped_column(String(64), default="GLOBAL_CANON")
    epistemic_status: Mapped[str] = mapped_column(String(64), default="OBSERVED")
    evidence_anchor_ids_json: Mapped[str] = mapped_column(Text, default="[]")


class TimelineEventModel(Base):
    __tablename__ = "timeline_events"

    event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    revision_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="")
    sequence_position: Mapped[int] = mapped_column(Integer, default=0)
    absolute_date: Mapped[str | None] = mapped_column(String(64), nullable=True)
    relative_time_expression: Mapped[str | None] = mapped_column(String(128), nullable=True)
    participant_entity_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    location_entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    consequences_json: Mapped[str] = mapped_column(Text, default="[]")
    evidence_anchor_ids_json: Mapped[str] = mapped_column(Text, default="[]")


class WorldRuleModel(Base):
    __tablename__ = "world_rules"

    rule_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    revision_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    rule_statement: Mapped[str] = mapped_column(Text, nullable=False)
    scope: Mapped[str] = mapped_column(String(64), default="GLOBAL")
    exceptions_json: Mapped[str] = mapped_column(Text, default="[]")
    evidence_anchor_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    canonical_status: Mapped[str] = mapped_column(String(32), default="AUTHOR_CONFIRMED")


class StoryThreadModel(Base):
    __tablename__ = "story_threads"

    thread_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    revision_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    introduced_at_anchor: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="OPEN")
    related_entity_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    update_anchor_ids_json: Mapped[str] = mapped_column(Text, default="[]")
