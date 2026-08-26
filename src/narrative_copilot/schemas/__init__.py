"""
Core schemas for Narrative Continuity Copilot.
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class PrivacyMode(str, Enum):
    LOCAL_ONLY = "LOCAL_ONLY"
    MINIMAL_CLOUD_CONTEXT = "MINIMAL_CLOUD_CONTEXT"


class UnitType(str, Enum):
    BOOK = "book"
    PART = "part"
    CHAPTER = "chapter"
    SCENE = "scene"
    BLOCK = "block"


class NarrativeScope(str, Enum):
    GLOBAL_CANON = "GLOBAL_CANON"
    POV_CHARACTER = "POV_CHARACTER"
    NARRATOR = "NARRATOR"
    SCENE_LOCAL = "SCENE_LOCAL"
    DREAM_OR_VISION = "DREAM_OR_VISION"
    HYPOTHETICAL = "HYPOTHETICAL"


class EpistemicStatus(str, Enum):
    OBSERVED = "OBSERVED"
    STATED_AS_FACT = "STATED_AS_FACT"
    BELIEVED = "BELIEVED"
    CLAIMED = "CLAIMED"
    RUMOR = "RUMOR"
    UNCERTAIN = "UNCERTAIN"
    DECEPTIVE_STATEMENT = "DECEPTIVE_STATEMENT"
    UNRELIABLE_NARRATION = "UNRELIABLE_NARRATION"


class CanonicalStatus(str, Enum):
    PROPOSED = "PROPOSED"
    AUTHOR_CONFIRMED = "AUTHOR_CONFIRMED"
    DISPUTED = "DISPUTED"
    INTENTIONAL_AMBIGUITY = "INTENTIONAL_AMBIGUITY"
    INTENTIONAL_CONTRADICTION = "INTENTIONAL_CONTRADICTION"
    SUPERSEDED = "SUPERSEDED"
    RESOLVED = "RESOLVED"
    IGNORED = "IGNORED"


class EntityType(str, Enum):
    CHARACTER = "character"
    LOCATION = "location"
    ORGANIZATION = "organization"
    OBJECT = "object"
    CREATURE = "creature"
    CONCEPT = "concept"


class ConflictClass(str, Enum):
    ATTRIBUTE_CONTRADICTION = "ATTRIBUTE_CONTRADICTION"
    RELATIONSHIP_CONTRADICTION = "RELATIONSHIP_CONTRADICTION"
    LOCATION_CONTINUITY = "LOCATION_CONTINUITY"
    OBJECT_STATE_CONTINUITY = "OBJECT_STATE_CONTINUITY"
    INJURY_OR_PHYSICAL_STATE = "INJURY_OR_PHYSICAL_STATE"
    TIMELINE_ORDER_CONTRADICTION = "TIMELINE_ORDER_CONTRADICTION"
    AGE_DATE_ARITHMETIC = "AGE_DATE_ARITHMETIC"
    KNOWLEDGE_STATE_LEAK = "KNOWLEDGE_STATE_LEAK"
    WORLD_RULE_VIOLATION = "WORLD_RULE_VIOLATION"
    IDENTITY_ALIAS_CONFLICT = "IDENTITY_ALIAS_CONFLICT"
    POV_OR_EPISTEMIC_CONFLICT = "POV_OR_EPISTEMIC_CONFLICT"
    THREAD_STATUS_INCONSISTENCY = "THREAD_STATUS_INCONSISTENCY"


class AuthorActionType(str, Enum):
    MARK_INTENTIONAL = "MARK_INTENTIONAL"
    MARK_POV_BELIEF = "MARK_POV_BELIEF"
    MARK_RUMOR = "MARK_RUMOR"
    MARK_UNRELIABLE = "MARK_UNRELIABLE"
    CREATE_WORLD_RULE_EXCEPTION = "CREATE_WORLD_RULE_EXCEPTION"
    RESOLVE_WITH_CURRENT_FACT = "RESOLVE_WITH_CURRENT_FACT"
    SUPERSEDE_EARLIER_FACT = "SUPERSEDE_EARLIER_FACT"
    MERGE_ALIASES = "MERGE_ALIASES"
    SPLIT_ENTITY = "SPLIT_ENTITY"
    IGNORE_ALERT = "IGNORE_ALERT"


class ThreadStatus(str, Enum):
    OPEN = "OPEN"
    DEVELOPING = "DEVELOPING"
    RESOLVED = "RESOLVED"
    ABANDONED = "ABANDONED"
    INTENTIONAL_OPEN_END = "INTENTIONAL_OPEN_END"


class ProviderStatus(str, Enum):
    IMPLEMENTED_AND_TESTED = "IMPLEMENTED_AND_TESTED"
    CONTRACT_TESTED = "CONTRACT_TESTED"
    LIVE_VALIDATED = "LIVE_VALIDATED"
    REFERENCE_ONLY = "REFERENCE_ONLY"
    NOT_EXECUTED = "NOT_EXECUTED"


class ManuscriptProject(BaseModel):
    project_id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    active_revision_id: str | None = None
    language: str = "en"
    genre_hint: str | None = None
    privacy_mode: PrivacyMode = PrivacyMode.LOCAL_ONLY


class ManuscriptRevision(BaseModel):
    revision_id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str
    parent_revision_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source_hash: str
    word_count: int = 0
    structure_version: int = 1


class StructuralUnit(BaseModel):
    unit_id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str
    revision_id: str
    unit_type: UnitType
    parent_id: str | None = None
    ordinal: int = 0
    title: str | None = None
    text: str = ""
    word_count: int = 0


class SourceAnchor(BaseModel):
    anchor_id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str
    revision_id: str
    chapter_id: str
    scene_id: str | None = None
    block_id: str
    char_start: int = 0
    char_end: int = 0
    text_hash: str
    normalized_quote: str
    previous_block_hash: str | None = None
    next_block_hash: str | None = None

    @field_validator("normalized_quote")
    @classmethod
    def validate_quote_length(cls, v: str) -> str:
        # Prevent normalized quote from being an entire manuscript copy
        if len(v) > 2000:
            return v[:2000] + "..."
        return v


class Entity(BaseModel):
    entity_id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str
    canonical_name: str
    entity_type: EntityType = EntityType.CHARACTER
    aliases: list[str] = Field(default_factory=list)
    description: str | None = None
    canonical_status: CanonicalStatus = CanonicalStatus.PROPOSED
    evidence_anchor_ids: list[str] = Field(default_factory=list)


class FactAssertion(BaseModel):
    fact_id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str
    revision_id: str
    subject_entity_id: str
    predicate: str
    object_entity_id: str | None = None
    value: str | None = None
    normalized_value: str | None = None
    temporal_scope: str = "GLOBAL"
    narrative_scope: NarrativeScope = NarrativeScope.GLOBAL_CANON
    epistemic_status: EpistemicStatus = EpistemicStatus.OBSERVED
    canonical_status: CanonicalStatus = CanonicalStatus.PROPOSED
    confidence: float = 1.0
    evidence_anchor_ids: list[str] = Field(default_factory=list)


class RelationAssertion(BaseModel):
    relation_id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str
    revision_id: str
    subject_entity_id: str
    relation_type: str
    object_entity_id: str
    temporal_validity: str = "GLOBAL"
    narrative_scope: NarrativeScope = NarrativeScope.GLOBAL_CANON
    epistemic_status: EpistemicStatus = EpistemicStatus.OBSERVED
    evidence_anchor_ids: list[str] = Field(default_factory=list)


class TimelineEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str
    revision_id: str
    title: str
    summary: str
    sequence_position: int = 0
    absolute_date: str | None = None
    relative_time_expression: str | None = None
    participant_entity_ids: list[str] = Field(default_factory=list)
    location_entity_id: str | None = None
    consequences: list[str] = Field(default_factory=list)
    evidence_anchor_ids: list[str] = Field(default_factory=list)


class WorldRule(BaseModel):
    rule_id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str
    revision_id: str
    rule_statement: str
    scope: str = "GLOBAL"
    exceptions: list[str] = Field(default_factory=list)
    evidence_anchor_ids: list[str] = Field(default_factory=list)
    canonical_status: CanonicalStatus = CanonicalStatus.AUTHOR_CONFIRMED


class StoryThread(BaseModel):
    thread_id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str
    revision_id: str
    description: str
    introduced_at_anchor: str
    status: ThreadStatus = ThreadStatus.OPEN
    related_entity_ids: list[str] = Field(default_factory=list)
    update_anchor_ids: list[str] = Field(default_factory=list)


class StoryMemory(BaseModel):
    project_id: str
    revision_id: str
    entities: list[Entity] = Field(default_factory=list)
    facts: list[FactAssertion] = Field(default_factory=list)
    relations: list[RelationAssertion] = Field(default_factory=list)
    timeline_events: list[TimelineEvent] = Field(default_factory=list)
    world_rules: list[WorldRule] = Field(default_factory=list)
    story_threads: list[StoryThread] = Field(default_factory=list)


class EvidenceSnippet(BaseModel):
    anchor_id: str
    chapter_id: str
    chapter_title: str | None = None
    scene_id: str | None = None
    block_id: str
    char_start: int
    char_end: int
    text_snippet: str
    revision_id: str


class ContinuityAlert(BaseModel):
    alert_id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str
    revision_id: str
    conflict_class: ConflictClass
    confidence: float = 0.95
    confidence_category: Literal["HIGH", "MEDIUM", "LOW", "INFORMATIONAL"] = "HIGH"
    explanation: str
    alternate_interpretations: list[str] = Field(default_factory=list)
    evidence_a: EvidenceSnippet
    evidence_b: EvidenceSnippet
    chapter_location: str | None = None
    requires_author_review: bool = True
    canonical_status: CanonicalStatus = CanonicalStatus.PROPOSED
    suppressed: bool = False
    decision_id: str | None = None


class AuthorDecision(BaseModel):
    decision_id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str
    alert_id: str
    action_type: AuthorActionType
    author_notes: str | None = None
    applied_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    parameters: dict[str, Any] = Field(default_factory=dict)
