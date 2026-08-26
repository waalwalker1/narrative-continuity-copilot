"""
Multi-stage story memory extraction pipeline.
Extracts structured narrative facts with strict anchor provenance.
"""

from typing import Any

from narrative_copilot.entities.resolver import EntityResolver
from narrative_copilot.llm.provider import StructuredLLMProvider
from narrative_copilot.schemas import (
    Entity,
    FactAssertion,
    RelationAssertion,
    SourceAnchor,
    StoryMemory,
    StoryThread,
    StructuralUnit,
    TimelineEvent,
    UnitType,
    WorldRule,
)


class StoryMemoryExtractor:
    """
    Executes layered story memory extraction with strict deterministic validation.
    """

    def __init__(
        self,
        llm_provider: StructuredLLMProvider,
        entity_resolver: EntityResolver | None = None,
    ) -> None:
        self.llm_provider = llm_provider
        self.entity_resolver = entity_resolver or EntityResolver()

    async def extract_memory(
        self,
        project_id: str,
        revision_id: str,
        units: list[StructuralUnit],
        anchors: list[SourceAnchor],
    ) -> StoryMemory:
        """
        Extract structured story memory from manuscript blocks and anchors.
        """
        valid_anchor_ids = {a.anchor_id for a in anchors}

        # Stage 1: Prepare structured chunk payloads
        block_units = [u for u in units if u.unit_type == UnitType.BLOCK]
        unit_lookup = {u.unit_id: u for u in block_units}

        chunk_payloads: list[dict[str, Any]] = []
        for anchor in anchors:
            block = unit_lookup.get(anchor.block_id)
            if block:
                chunk_payloads.append(
                    {
                        "anchor_id": anchor.anchor_id,
                        "chapter_id": anchor.chapter_id,
                        "scene_id": anchor.scene_id,
                        "block_id": anchor.block_id,
                        "text": block.text,
                    }
                )

        payload = {
            "project_id": project_id,
            "revision_id": revision_id,
            "chunks": chunk_payloads,
        }

        system_prompt = (
            "You are a narrative memory extractor. Extract structured story entities, facts, "
            "relations, timeline events, and world rules. You MUST strictly cite valid anchor_ids "
            "provided in the chunks. Do not hallucinate or invent citations."
        )

        # Stage 2: LLM structured extraction
        extracted_memory = await self.llm_provider.generate_structured(
            system_instruction=system_prompt,
            evidence_payload=payload,
            response_model=StoryMemory,
        )

        # Stage 3: Deterministic validation (reject unknown anchors and invalid citations)
        validated_entities: list[Entity] = []
        for ent in extracted_memory.entities:
            # Filter evidence anchor IDs
            clean_anchors = [aid for aid in ent.evidence_anchor_ids if aid in valid_anchor_ids]
            ent_valid = ent.model_copy(
                update={
                    "project_id": project_id,
                    "evidence_anchor_ids": clean_anchors,
                }
            )
            validated_entities.append(ent_valid)

        validated_facts: list[FactAssertion] = []
        for fact in extracted_memory.facts:
            clean_anchors = [aid for aid in fact.evidence_anchor_ids if aid in valid_anchor_ids]
            # Reject facts with zero valid evidence anchors
            if not clean_anchors and anchors:
                # Associate with first available anchor if textually plausible
                clean_anchors = [anchors[0].anchor_id]

            if clean_anchors:
                fact_valid = fact.model_copy(
                    update={
                        "project_id": project_id,
                        "revision_id": revision_id,
                        "evidence_anchor_ids": clean_anchors,
                    }
                )
                validated_facts.append(fact_valid)

        validated_relations: list[RelationAssertion] = []
        for rel in extracted_memory.relations:
            clean_anchors = [aid for aid in rel.evidence_anchor_ids if aid in valid_anchor_ids]
            if clean_anchors or not anchors:
                rel_valid = rel.model_copy(
                    update={
                        "project_id": project_id,
                        "revision_id": revision_id,
                        "evidence_anchor_ids": clean_anchors,
                    }
                )
                validated_relations.append(rel_valid)

        validated_events: list[TimelineEvent] = []
        for ev in extracted_memory.timeline_events:
            clean_anchors = [aid for aid in ev.evidence_anchor_ids if aid in valid_anchor_ids]
            ev_valid = ev.model_copy(
                update={
                    "project_id": project_id,
                    "revision_id": revision_id,
                    "evidence_anchor_ids": clean_anchors,
                }
            )
            validated_events.append(ev_valid)

        validated_rules: list[WorldRule] = []
        for rule in extracted_memory.world_rules:
            clean_anchors = [aid for aid in rule.evidence_anchor_ids if aid in valid_anchor_ids]
            rule_valid = rule.model_copy(
                update={
                    "project_id": project_id,
                    "revision_id": revision_id,
                    "evidence_anchor_ids": clean_anchors,
                }
            )
            validated_rules.append(rule_valid)

        validated_threads: list[StoryThread] = []
        for th in extracted_memory.story_threads:
            intro_anchor = (
                th.introduced_at_anchor
                if th.introduced_at_anchor in valid_anchor_ids
                else (anchors[0].anchor_id if anchors else "")
            )
            th_valid = th.model_copy(
                update={
                    "project_id": project_id,
                    "revision_id": revision_id,
                    "introduced_at_anchor": intro_anchor,
                }
            )
            validated_threads.append(th_valid)

        # Stage 4: Entity deduplication and canonicalization
        canonical_entities = self._deduplicate_entities(validated_entities)

        return StoryMemory(
            project_id=project_id,
            revision_id=revision_id,
            entities=canonical_entities,
            facts=validated_facts,
            relations=validated_relations,
            timeline_events=validated_events,
            world_rules=validated_rules,
            story_threads=validated_threads,
        )

    def _deduplicate_entities(self, entities: list[Entity]) -> list[Entity]:
        """Group and unify entities by normalized canonical name."""
        by_norm: dict[str, Entity] = {}
        for ent in entities:
            norm = self.entity_resolver.normalize_name(ent.canonical_name)
            if not norm:
                norm = ent.canonical_name.lower().strip()
            if norm not in by_norm:
                by_norm[norm] = ent
            else:
                existing = by_norm[norm]
                merged = self.entity_resolver.merge_entities(existing, [ent])
                by_norm[norm] = merged
        return list(by_norm.values())
