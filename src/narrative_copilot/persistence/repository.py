"""
Repository layer for persistence of narrative copilot entities, anchors, and workflows.
"""

import json

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from narrative_copilot.persistence.models import (
    AuthorDecisionModel,
    ContinuityAlertModel,
    EntityModel,
    FactModel,
    ProjectModel,
    RelationModel,
    RevisionModel,
    SourceAnchorModel,
    StoryThreadModel,
    StructuralUnitModel,
    TimelineEventModel,
    WorldRuleModel,
)
from narrative_copilot.schemas import (
    AuthorActionType,
    AuthorDecision,
    CanonicalStatus,
    ConflictClass,
    ContinuityAlert,
    Entity,
    EntityType,
    EpistemicStatus,
    EvidenceSnippet,
    FactAssertion,
    ManuscriptProject,
    ManuscriptRevision,
    NarrativeScope,
    PrivacyMode,
    RelationAssertion,
    SourceAnchor,
    StoryThread,
    StructuralUnit,
    ThreadStatus,
    TimelineEvent,
    UnitType,
    WorldRule,
)


class Repository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # --- Project Methods ---
    async def create_project(self, project: ManuscriptProject) -> ManuscriptProject:
        model = ProjectModel(
            project_id=project.project_id,
            title=project.title,
            created_at=project.created_at,
            active_revision_id=project.active_revision_id,
            language=project.language,
            genre_hint=project.genre_hint,
            privacy_mode=project.privacy_mode.value,
        )
        self.session.add(model)
        await self.session.commit()
        return project

    async def update_project_active_revision(self, project_id: str, revision_id: str) -> None:
        stmt = select(ProjectModel).where(ProjectModel.project_id == project_id)
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        if row:
            row.active_revision_id = revision_id
            await self.session.commit()

    async def get_project(self, project_id: str) -> ManuscriptProject | None:
        stmt = select(ProjectModel).where(ProjectModel.project_id == project_id)
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        if not row:
            return None
        return ManuscriptProject(
            project_id=row.project_id,
            title=row.title,
            created_at=row.created_at,
            active_revision_id=row.active_revision_id,
            language=row.language,
            genre_hint=row.genre_hint,
            privacy_mode=PrivacyMode(row.privacy_mode),
        )

    async def list_projects(self) -> list[ManuscriptProject]:
        stmt = select(ProjectModel).order_by(ProjectModel.created_at.desc())
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [
            ManuscriptProject(
                project_id=r.project_id,
                title=r.title,
                created_at=r.created_at,
                active_revision_id=r.active_revision_id,
                language=r.language,
                genre_hint=r.genre_hint,
                privacy_mode=PrivacyMode(r.privacy_mode),
            )
            for r in rows
        ]

    # --- Revision Methods ---
    async def create_revision(
        self, revision: ManuscriptRevision, raw_markdown: str = ""
    ) -> ManuscriptRevision:
        model = RevisionModel(
            revision_id=revision.revision_id,
            project_id=revision.project_id,
            parent_revision_id=revision.parent_revision_id,
            created_at=revision.created_at,
            source_hash=revision.source_hash,
            word_count=revision.word_count,
            structure_version=revision.structure_version,
            raw_markdown=raw_markdown,
        )
        self.session.add(model)
        # Update active revision on project
        await self.session.execute(
            update(ProjectModel)
            .where(ProjectModel.project_id == revision.project_id)
            .values(active_revision_id=revision.revision_id)
        )
        await self.session.commit()
        return revision

    async def get_revision(self, revision_id: str) -> ManuscriptRevision | None:
        stmt = select(RevisionModel).where(RevisionModel.revision_id == revision_id)
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        if not row:
            return None
        return ManuscriptRevision(
            revision_id=row.revision_id,
            project_id=row.project_id,
            parent_revision_id=row.parent_revision_id,
            created_at=row.created_at,
            source_hash=row.source_hash,
            word_count=row.word_count,
            structure_version=row.structure_version,
        )

    # --- Structural Units & Anchors ---
    async def save_structural_units(self, units: list[StructuralUnit]) -> None:
        models = [
            StructuralUnitModel(
                unit_id=u.unit_id,
                project_id=u.project_id,
                revision_id=u.revision_id,
                unit_type=u.unit_type.value,
                parent_id=u.parent_id,
                ordinal=u.ordinal,
                title=u.title,
                text=u.text,
                word_count=u.word_count,
            )
            for u in units
        ]
        self.session.add_all(models)
        await self.session.commit()

    async def get_structural_units(self, revision_id: str) -> list[StructuralUnit]:
        stmt = (
            select(StructuralUnitModel)
            .where(StructuralUnitModel.revision_id == revision_id)
            .order_by(StructuralUnitModel.ordinal)
        )
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [
            StructuralUnit(
                unit_id=r.unit_id,
                project_id=r.project_id,
                revision_id=r.revision_id,
                unit_type=UnitType(r.unit_type),
                parent_id=r.parent_id,
                ordinal=r.ordinal,
                title=r.title,
                text=r.text,
                word_count=r.word_count,
            )
            for r in rows
        ]

    async def save_anchors(self, anchors: list[SourceAnchor]) -> None:
        models = [
            SourceAnchorModel(
                anchor_id=a.anchor_id,
                project_id=a.project_id,
                revision_id=a.revision_id,
                chapter_id=a.chapter_id,
                scene_id=a.scene_id,
                block_id=a.block_id,
                char_start=a.char_start,
                char_end=a.char_end,
                text_hash=a.text_hash,
                normalized_quote=a.normalized_quote,
                previous_block_hash=a.previous_block_hash,
                next_block_hash=a.next_block_hash,
            )
            for a in anchors
        ]
        self.session.add_all(models)
        await self.session.commit()

    async def get_anchors(self, revision_id: str) -> list[SourceAnchor]:
        stmt = select(SourceAnchorModel).where(SourceAnchorModel.revision_id == revision_id)
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [
            SourceAnchor(
                anchor_id=r.anchor_id,
                project_id=r.project_id,
                revision_id=r.revision_id,
                chapter_id=r.chapter_id,
                scene_id=r.scene_id,
                block_id=r.block_id,
                char_start=r.char_start,
                char_end=r.char_end,
                text_hash=r.text_hash,
                normalized_quote=r.normalized_quote,
                previous_block_hash=r.previous_block_hash,
                next_block_hash=r.next_block_hash,
            )
            for r in rows
        ]

    # --- Story Memory ---
    async def save_entities(self, entities: list[Entity]) -> None:
        models = [
            EntityModel(
                entity_id=e.entity_id,
                project_id=e.project_id,
                canonical_name=e.canonical_name,
                entity_type=e.entity_type.value,
                aliases_json=json.dumps(e.aliases),
                description=e.description,
                canonical_status=e.canonical_status.value,
                evidence_anchor_ids_json=json.dumps(e.evidence_anchor_ids),
            )
            for e in entities
        ]
        self.session.add_all(models)
        await self.session.commit()

    async def get_entities(self, project_id: str) -> list[Entity]:
        stmt = select(EntityModel).where(EntityModel.project_id == project_id)
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [
            Entity(
                entity_id=r.entity_id,
                project_id=r.project_id,
                canonical_name=r.canonical_name,
                entity_type=EntityType(r.entity_type),
                aliases=json.loads(r.aliases_json),
                description=r.description,
                canonical_status=CanonicalStatus(r.canonical_status),
                evidence_anchor_ids=json.loads(r.evidence_anchor_ids_json),
            )
            for r in rows
        ]

    async def save_facts(self, facts: list[FactAssertion]) -> None:
        models = [
            FactModel(
                fact_id=f.fact_id,
                project_id=f.project_id,
                revision_id=f.revision_id,
                subject_entity_id=f.subject_entity_id,
                predicate=f.predicate,
                object_entity_id=f.object_entity_id,
                value=f.value,
                normalized_value=f.normalized_value,
                temporal_scope=f.temporal_scope,
                narrative_scope=f.narrative_scope.value,
                epistemic_status=f.epistemic_status.value,
                canonical_status=f.canonical_status.value,
                confidence=f.confidence,
                evidence_anchor_ids_json=json.dumps(f.evidence_anchor_ids),
            )
            for f in facts
        ]
        self.session.add_all(models)
        await self.session.commit()

    async def get_facts(self, revision_id: str) -> list[FactAssertion]:
        stmt = select(FactModel).where(FactModel.revision_id == revision_id)
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [
            FactAssertion(
                fact_id=r.fact_id,
                project_id=r.project_id,
                revision_id=r.revision_id,
                subject_entity_id=r.subject_entity_id,
                predicate=r.predicate,
                object_entity_id=r.object_entity_id,
                value=r.value,
                normalized_value=r.normalized_value,
                temporal_scope=r.temporal_scope,
                narrative_scope=NarrativeScope(r.narrative_scope),
                epistemic_status=EpistemicStatus(r.epistemic_status),
                canonical_status=CanonicalStatus(r.canonical_status),
                confidence=r.confidence,
                evidence_anchor_ids=json.loads(r.evidence_anchor_ids_json),
            )
            for r in rows
        ]

    async def save_relations(self, relations: list[RelationAssertion]) -> None:
        models = [
            RelationModel(
                relation_id=r.relation_id,
                project_id=r.project_id,
                revision_id=r.revision_id,
                subject_entity_id=r.subject_entity_id,
                relation_type=r.relation_type,
                object_entity_id=r.object_entity_id,
                temporal_validity=r.temporal_validity,
                narrative_scope=r.narrative_scope.value,
                epistemic_status=r.epistemic_status.value,
                evidence_anchor_ids_json=json.dumps(r.evidence_anchor_ids),
            )
            for r in relations
        ]
        self.session.add_all(models)
        await self.session.commit()

    async def get_relations(self, revision_id: str) -> list[RelationAssertion]:
        stmt = select(RelationModel).where(RelationModel.revision_id == revision_id)
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [
            RelationAssertion(
                relation_id=r.relation_id,
                project_id=r.project_id,
                revision_id=r.revision_id,
                subject_entity_id=r.subject_entity_id,
                relation_type=r.relation_type,
                object_entity_id=r.object_entity_id,
                temporal_validity=r.temporal_validity,
                narrative_scope=NarrativeScope(r.narrative_scope),
                epistemic_status=EpistemicStatus(r.epistemic_status),
                evidence_anchor_ids=json.loads(r.evidence_anchor_ids_json),
            )
            for r in rows
        ]

    async def save_timeline_events(self, events: list[TimelineEvent]) -> None:
        models = [
            TimelineEventModel(
                event_id=e.event_id,
                project_id=e.project_id,
                revision_id=e.revision_id,
                title=e.title,
                summary=e.summary,
                sequence_position=e.sequence_position,
                absolute_date=e.absolute_date,
                relative_time_expression=e.relative_time_expression,
                participant_entity_ids_json=json.dumps(e.participant_entity_ids),
                location_entity_id=e.location_entity_id,
                consequences_json=json.dumps(e.consequences),
                evidence_anchor_ids_json=json.dumps(e.evidence_anchor_ids),
            )
            for e in events
        ]
        self.session.add_all(models)
        await self.session.commit()

    async def get_timeline_events(self, revision_id: str) -> list[TimelineEvent]:
        stmt = select(TimelineEventModel).where(TimelineEventModel.revision_id == revision_id).order_by(TimelineEventModel.sequence_position)
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [
            TimelineEvent(
                event_id=r.event_id,
                project_id=r.project_id,
                revision_id=r.revision_id,
                title=r.title,
                summary=r.summary,
                sequence_position=r.sequence_position,
                absolute_date=r.absolute_date,
                relative_time_expression=r.relative_time_expression,
                participant_entity_ids=json.loads(r.participant_entity_ids_json),
                location_entity_id=r.location_entity_id,
                consequences=json.loads(r.consequences_json),
                evidence_anchor_ids=json.loads(r.evidence_anchor_ids_json),
            )
            for r in rows
        ]

    async def save_world_rules(self, rules: list[WorldRule]) -> None:
        models = [
            WorldRuleModel(
                rule_id=w.rule_id,
                project_id=w.project_id,
                revision_id=w.revision_id,
                rule_statement=w.rule_statement,
                scope=w.scope,
                exceptions_json=json.dumps(w.exceptions),
                evidence_anchor_ids_json=json.dumps(w.evidence_anchor_ids),
                canonical_status=w.canonical_status.value,
            )
            for w in rules
        ]
        self.session.add_all(models)
        await self.session.commit()

    async def get_world_rules(self, revision_id: str) -> list[WorldRule]:
        stmt = select(WorldRuleModel).where(WorldRuleModel.revision_id == revision_id)
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [
            WorldRule(
                rule_id=r.rule_id,
                project_id=r.project_id,
                revision_id=r.revision_id,
                rule_statement=r.rule_statement,
                scope=r.scope,
                exceptions=json.loads(r.exceptions_json),
                evidence_anchor_ids=json.loads(r.evidence_anchor_ids_json),
                canonical_status=CanonicalStatus(r.canonical_status),
            )
            for r in rows
        ]

    async def save_story_threads(self, threads: list[StoryThread]) -> None:
        models = [
            StoryThreadModel(
                thread_id=t.thread_id,
                project_id=t.project_id,
                revision_id=t.revision_id,
                description=t.description,
                introduced_at_anchor=t.introduced_at_anchor,
                status=t.status.value,
                related_entity_ids_json=json.dumps(t.related_entity_ids),
                update_anchor_ids_json=json.dumps(t.update_anchor_ids),
            )
            for t in threads
        ]
        self.session.add_all(models)
        await self.session.commit()

    async def get_story_threads(self, revision_id: str) -> list[StoryThread]:
        stmt = select(StoryThreadModel).where(StoryThreadModel.revision_id == revision_id)
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [
            StoryThread(
                thread_id=r.thread_id,
                project_id=r.project_id,
                revision_id=r.revision_id,
                description=r.description,
                introduced_at_anchor=r.introduced_at_anchor,
                status=ThreadStatus(r.status),
                related_entity_ids=json.loads(r.related_entity_ids_json),
                update_anchor_ids=json.loads(r.update_anchor_ids_json),
            )
            for r in rows
        ]

    # --- Alerts & Author Decisions ---
    async def save_alerts(self, alerts: list[ContinuityAlert]) -> None:
        models = [
            ContinuityAlertModel(
                alert_id=a.alert_id,
                project_id=a.project_id,
                revision_id=a.revision_id,
                conflict_class=a.conflict_class.value,
                confidence=a.confidence,
                confidence_category=a.confidence_category,
                explanation=a.explanation,
                alternate_interpretations_json=json.dumps(a.alternate_interpretations),
                evidence_a_json=a.evidence_a.model_dump_json(),
                evidence_b_json=a.evidence_b.model_dump_json(),
                chapter_location=a.chapter_location,
                requires_author_review=a.requires_author_review,
                canonical_status=a.canonical_status.value,
                suppressed=a.suppressed,
                decision_id=a.decision_id,
            )
            for a in alerts
        ]
        self.session.add_all(models)
        await self.session.commit()

    async def get_alerts(
        self, project_id: str, revision_id: str | None = None
    ) -> list[ContinuityAlert]:
        stmt = select(ContinuityAlertModel).where(ContinuityAlertModel.project_id == project_id)
        if revision_id:
            stmt = stmt.where(ContinuityAlertModel.revision_id == revision_id)
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [
            ContinuityAlert(
                alert_id=r.alert_id,
                project_id=r.project_id,
                revision_id=r.revision_id,
                conflict_class=ConflictClass(r.conflict_class),
                confidence=r.confidence,
                confidence_category=r.confidence_category,  # type: ignore[arg-type]
                explanation=r.explanation,
                alternate_interpretations=json.loads(r.alternate_interpretations_json),
                evidence_a=EvidenceSnippet.model_validate_json(r.evidence_a_json),
                evidence_b=EvidenceSnippet.model_validate_json(r.evidence_b_json),
                chapter_location=r.chapter_location,
                requires_author_review=r.requires_author_review,
                canonical_status=CanonicalStatus(r.canonical_status),
                suppressed=r.suppressed,
                decision_id=r.decision_id,
            )
            for r in rows
        ]

    async def record_author_decision(self, decision: AuthorDecision) -> None:
        model = AuthorDecisionModel(
            decision_id=decision.decision_id,
            project_id=decision.project_id,
            alert_id=decision.alert_id,
            action_type=decision.action_type.value,
            author_notes=decision.author_notes,
            applied_at=decision.applied_at,
            parameters_json=json.dumps(decision.parameters),
        )
        self.session.add(model)
        # Update alert status based on author decision
        canonical_map = {
            AuthorActionType.MARK_INTENTIONAL: CanonicalStatus.INTENTIONAL_CONTRADICTION,
            AuthorActionType.MARK_POV_BELIEF: CanonicalStatus.AUTHOR_CONFIRMED,
            AuthorActionType.MARK_RUMOR: CanonicalStatus.AUTHOR_CONFIRMED,
            AuthorActionType.MARK_UNRELIABLE: CanonicalStatus.AUTHOR_CONFIRMED,
            AuthorActionType.CREATE_WORLD_RULE_EXCEPTION: CanonicalStatus.AUTHOR_CONFIRMED,
            AuthorActionType.RESOLVE_WITH_CURRENT_FACT: CanonicalStatus.RESOLVED,
            AuthorActionType.SUPERSEDE_EARLIER_FACT: CanonicalStatus.SUPERSEDED,
            AuthorActionType.IGNORE_ALERT: CanonicalStatus.IGNORED,
        }
        new_status = canonical_map.get(decision.action_type, CanonicalStatus.AUTHOR_CONFIRMED)
        await self.session.execute(
            update(ContinuityAlertModel)
            .where(ContinuityAlertModel.alert_id == decision.alert_id)
            .values(
                canonical_status=new_status.value,
                suppressed=True,
                decision_id=decision.decision_id,
            )
        )
        await self.session.commit()

    async def get_author_decisions(self, project_id: str) -> list[AuthorDecision]:
        stmt = select(AuthorDecisionModel).where(AuthorDecisionModel.project_id == project_id)
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [
            AuthorDecision(
                decision_id=r.decision_id,
                project_id=r.project_id,
                alert_id=r.alert_id,
                action_type=AuthorActionType(r.action_type),
                author_notes=r.author_notes,
                applied_at=r.applied_at,
                parameters=json.loads(r.parameters_json),
            )
            for r in rows
        ]

    async def delete_memory_for_revision(self, revision_id: str) -> None:
        await self.session.execute(delete(FactModel).where(FactModel.revision_id == revision_id))
        await self.session.execute(delete(RelationModel).where(RelationModel.revision_id == revision_id))
        await self.session.execute(delete(TimelineEventModel).where(TimelineEventModel.revision_id == revision_id))
        await self.session.execute(delete(WorldRuleModel).where(WorldRuleModel.revision_id == revision_id))
        await self.session.execute(delete(StoryThreadModel).where(StoryThreadModel.revision_id == revision_id))
        await self.session.commit()

    async def delete_anchors_and_units_for_blocks(self, revision_id: str, block_ids: list[str]) -> None:
        if not block_ids:
            return
        await self.session.execute(
            delete(SourceAnchorModel).where(
                SourceAnchorModel.revision_id == revision_id,
                SourceAnchorModel.block_id.in_(block_ids),
            )
        )
        await self.session.execute(
            delete(StructuralUnitModel).where(
                StructuralUnitModel.revision_id == revision_id,
                StructuralUnitModel.unit_id.in_(block_ids),
            )
        )
        await self.session.commit()
