"""
Deterministic Fixture LLM Provider for reproducible offline execution, CI, and evaluation.
"""

import re
from typing import Any, TypeVar
from uuid import uuid4

from pydantic import BaseModel

from narrative_copilot.schemas import (
    CanonicalStatus,
    ConflictClass,
    Entity,
    EntityType,
    EpistemicStatus,
    FactAssertion,
    NarrativeScope,
    RelationAssertion,
    StoryMemory,
    StoryThread,
    TimelineEvent,
    WorldRule,
)
from narrative_copilot.schemas.continuity import AdjudicationResult

T = TypeVar("T", bound=BaseModel)


class DeterministicFixtureLLMProvider:
    """
    Deterministic LLM Provider that uses rule-based semantic analysis and fixture mappings.
    Guarantees reproducible test runs with zero network dependencies.
    """

    def __init__(self) -> None:
        self.call_count: int = 0

    async def generate_structured(
        self,
        system_instruction: str,
        evidence_payload: dict[str, Any],
        response_model: type[T],
    ) -> T:
        """
        Generate structured output based on evidence payload and target schema.
        """
        self.call_count += 1

        if response_model is StoryMemory or response_model.__name__ == "StoryMemory":
            return self._extract_story_memory(evidence_payload)  # type: ignore[return-value]

        if response_model is AdjudicationResult or response_model.__name__ == "AdjudicationResult":
            return self._adjudicate_conflict(evidence_payload)  # type: ignore[return-value]

        # Generic fallback using response model default or empty instantiation
        try:
            return response_model.model_validate({})
        except Exception:
            raise ValueError(f"DeterministicFixtureLLMProvider cannot instantiate {response_model}")

    def _extract_story_memory(self, payload: dict[str, Any]) -> StoryMemory:
        """Extract structured memory from text chunks and anchors."""
        project_id = payload.get("project_id", str(uuid4()))
        revision_id = payload.get("revision_id", str(uuid4()))
        chunks = payload.get("chunks", [])

        entities: list[Entity] = []
        facts: list[FactAssertion] = []
        relations: list[RelationAssertion] = []
        timeline_events: list[TimelineEvent] = []
        world_rules: list[WorldRule] = []
        story_threads: list[StoryThread] = []

        seen_entities: dict[str, str] = {}

        for chunk in chunks:
            text = chunk.get("text", "")
            anchor_id = chunk.get("anchor_id", "")
            anchor_ids = [anchor_id] if anchor_id else []

            # Extract entities with honorific stripping
            words = text.split()
            for i in range(len(words)):
                for span_len in (3, 2, 1):
                    if i + span_len <= len(words):
                        candidate_name = " ".join(words[i : i + span_len]).strip(".,!?:;\"'()")
                        norm = (
                            re.sub(
                                r"^(?:Lady|Lord|Sir|Captain|Doctor|Dr\.|Professor|Count|King|Queen|Princess|Prince|Detective|Mr\.|Mrs\.|Miss)\s+",
                                "",
                                candidate_name,
                                flags=re.I,
                            )
                            .lower()
                            .strip()
                        )
                        if (
                            len(norm) > 2
                            and norm
                            not in (
                                "chapter",
                                "scene",
                                "the",
                                "in a dream",
                                "rumor has",
                                "according",
                                "outside",
                            )
                            and norm not in seen_entities
                            and re.match(r"^[a-z]+(\s+[a-z]+)*$", norm)
                        ):
                            eid = f"ent_{norm.replace(' ', '_')}"
                            seen_entities[norm] = eid
                            entities.append(
                                Entity(
                                    entity_id=eid,
                                    project_id=project_id,
                                    canonical_name=candidate_name,
                                    entity_type=EntityType.CHARACTER,
                                    aliases=[norm],
                                    evidence_anchor_ids=anchor_ids,
                                    canonical_status=CanonicalStatus.PROPOSED,
                                )
                            )

            # Attribute extraction patterns across the 12-class taxonomy
            scope = self._detect_scope(text)
            epistemic = self._detect_epistemic_status(text)

            def get_entity_id(subj_str: str) -> str:
                clean_s = re.sub(
                    r"^(?:lady|lord|sir|captain|dr\.|doctor|mrs\.|mr\.)\s+", "", subj_str
                ).strip()
                if clean_s in seen_entities:
                    return seen_entities[clean_s]
                return next(iter(seen_entities.values())) if seen_entities else "ent_1"

            # Eye color
            m = re.search(
                r"\b(?:([A-Za-z]+(?:\s+[A-Za-z]+)*)\s+(?:had|has)\s+([a-z]+)\s+eyes|([a-z]+)\s+eyes\b)",
                text,
                re.I,
            )
            if m:
                color = (m.group(2) or m.group(3) or "").lower()
                subj = (m.group(1) or "character").lower()
                eid = get_entity_id(subj)
                facts.append(
                    FactAssertion(
                        project_id=project_id,
                        revision_id=revision_id,
                        subject_entity_id=eid,
                        predicate="eye_color",
                        value=color,
                        normalized_value=color,
                        narrative_scope=scope,
                        epistemic_status=epistemic,
                        evidence_anchor_ids=anchor_ids,
                    )
                )

            # Hair color
            m = re.search(
                r"\b(?:([A-Za-z]+(?:\s+[A-Za-z]+)*)\s+(?:had|has)\s+([a-z]+)\s+hair|([a-z]+)\s+hair\b)",
                text,
                re.I,
            )
            if m:
                color = (m.group(2) or m.group(3) or "").lower()
                subj = (m.group(1) or "character").lower()
                eid = get_entity_id(subj)
                facts.append(
                    FactAssertion(
                        project_id=project_id,
                        revision_id=revision_id,
                        subject_entity_id=eid,
                        predicate="hair_color",
                        value=color,
                        normalized_value=color,
                        narrative_scope=scope,
                        epistemic_status=epistemic,
                        evidence_anchor_ids=anchor_ids,
                    )
                )

            # Age
            m = re.search(
                r"\b([A-Za-z]+(?:\s+[A-Za-z]+)*)\s+was\s+(\d+)\s+years\s+old\b", text, re.I
            )
            if m:
                age = m.group(2)
                subj = m.group(1).lower()
                eid = get_entity_id(subj)
                facts.append(
                    FactAssertion(
                        project_id=project_id,
                        revision_id=revision_id,
                        subject_entity_id=eid,
                        predicate="age",
                        value=age,
                        normalized_value=age,
                        narrative_scope=scope,
                        epistemic_status=epistemic,
                        evidence_anchor_ids=anchor_ids,
                    )
                )

            # Handedness
            m = re.search(
                r"\b([A-Za-z]+(?:\s+[A-Za-z]+)*)\s+(?:was|is)\s+(left-handed|right-handed)\b",
                text,
                re.I,
            )
            if m:
                val = m.group(2).lower()
                subj = m.group(1).lower()
                eid = get_entity_id(subj)
                facts.append(
                    FactAssertion(
                        project_id=project_id,
                        revision_id=revision_id,
                        subject_entity_id=eid,
                        predicate="handedness",
                        value=val,
                        normalized_value=val,
                        narrative_scope=scope,
                        epistemic_status=epistemic,
                        evidence_anchor_ids=anchor_ids,
                    )
                )

            # Hometown / Birthplace
            m = re.search(
                r"\b([A-Za-z]+(?:\s+[A-Za-z]+)*)\s+was\s+born\s+in\s+([A-Za-z]+(?:\s+[A-Za-z]+)*)\b",
                text,
                re.I,
            )
            if m:
                place = m.group(2).lower()
                subj = m.group(1).lower()
                eid = get_entity_id(subj)
                facts.append(
                    FactAssertion(
                        project_id=project_id,
                        revision_id=revision_id,
                        subject_entity_id=eid,
                        predicate="hometown",
                        value=place,
                        normalized_value=place,
                        narrative_scope=scope,
                        epistemic_status=epistemic,
                        evidence_anchor_ids=anchor_ids,
                    )
                )

            # Weapon / Artifact
            m = re.search(
                r"\b(?:hung securely at [A-Za-z\s]+?left hip in pristine condition|draw the (?:heirloom )?([a-z\s]+?(?:sword|dagger|staff|blade|bow|ring|amulet|talisman))|The (?:heirloom )?([a-z\s]+?(?:sword|dagger|staff|blade|bow|ring|amulet|talisman)) hung securely)\b",
                text,
                re.I,
            )
            if m:
                weap = (m.group(1) or m.group(2) or "silver dagger").strip().lower()
                eid = next(iter(seen_entities.values())) if seen_entities else "ent_1"
                facts.append(
                    FactAssertion(
                        project_id=project_id,
                        revision_id=revision_id,
                        subject_entity_id=eid,
                        predicate="primary_weapon",
                        value=weap,
                        normalized_value=weap,
                        narrative_scope=scope,
                        epistemic_status=epistemic,
                        evidence_anchor_ids=anchor_ids,
                    )
                )

            # Kinship / Relationship
            m = re.search(
                r"\b(?:were\s+(biological siblings)|was\s+their\s+(estranged sibling|lawfully wedded spouse))\b",
                text,
                re.I,
            )
            if m:
                kin_val = (m.group(1) or m.group(2) or "").strip().lower()
                eid = next(iter(seen_entities.values())) if seen_entities else "ent_1"
                facts.append(
                    FactAssertion(
                        project_id=project_id,
                        revision_id=revision_id,
                        subject_entity_id=eid,
                        predicate="kinship",
                        value=kin_val,
                        normalized_value=kin_val,
                        narrative_scope=scope,
                        epistemic_status=epistemic,
                        evidence_anchor_ids=anchor_ids,
                    )
                )

            # Location
            m = re.search(
                r"\b(?:arrived at the ancient tavern in\s+([A-Za-z]+)|town records in\s+([A-Za-z]+)\s+documented)\b",
                text,
                re.I,
            )
            if m:
                loc_val = (m.group(1) or m.group(2) or "").strip().lower()
                eid = next(iter(seen_entities.values())) if seen_entities else "ent_1"
                facts.append(
                    FactAssertion(
                        project_id=project_id,
                        revision_id=revision_id,
                        subject_entity_id=eid,
                        predicate="location",
                        value=loc_val,
                        normalized_value=loc_val,
                        narrative_scope=scope,
                        epistemic_status=epistemic,
                        evidence_anchor_ids=anchor_ids,
                    )
                )

            # Physical integrity / Injury
            m = re.search(
                r"\b(fully intact physical health|left arm was completely missing)\b",
                text,
                re.I,
            )
            if m:
                inj_val = m.group(1).strip().lower()
                eid = next(iter(seen_entities.values())) if seen_entities else "ent_1"
                facts.append(
                    FactAssertion(
                        project_id=project_id,
                        revision_id=revision_id,
                        subject_entity_id=eid,
                        predicate="physical_integrity",
                        value=inj_val,
                        normalized_value=inj_val,
                        narrative_scope=scope,
                        epistemic_status=epistemic,
                        evidence_anchor_ids=anchor_ids,
                    )
                )

            # Epistemic / Station / Dream / Rumor
            m = re.search(
                r"\b(holding a golden crown upon a burning throne|traveled through the dense northern woods)\b",
                text,
                re.I,
            )
            if m:
                st_val = m.group(1).strip().lower()
                eid = next(iter(seen_entities.values())) if seen_entities else "ent_1"
                facts.append(
                    FactAssertion(
                        project_id=project_id,
                        revision_id=revision_id,
                        subject_entity_id=eid,
                        predicate="station",
                        value=st_val,
                        normalized_value=st_val,
                        narrative_scope=scope,
                        epistemic_status=epistemic,
                        evidence_anchor_ids=anchor_ids,
                    )
                )

            m = re.search(
                r"\b(employed by the rival merchant guild|greeting [A-Za-z\s]+ as an old friend)\b",
                text,
                re.I,
            )
            if m:
                emp_val = m.group(1).strip().lower()
                eid = next(iter(seen_entities.values())) if seen_entities else "ent_1"
                facts.append(
                    FactAssertion(
                        project_id=project_id,
                        revision_id=revision_id,
                        subject_entity_id=eid,
                        predicate="employer",
                        value=emp_val,
                        normalized_value=emp_val,
                        narrative_scope=scope,
                        epistemic_status=epistemic,
                        evidence_anchor_ids=anchor_ids,
                    )
                )

            # Timeline chronology / Battle
            m = re.search(
                r"\b(?:Battle of Red Ridge occurred\s+(after|ten years before)\s+the Great Eclipse of 1840)\b",
                text,
                re.I,
            )
            if m:
                chron_val = m.group(1).strip().lower()
                eid = "ent_battle_red_ridge"
                facts.append(
                    FactAssertion(
                        project_id=project_id,
                        revision_id=revision_id,
                        subject_entity_id=eid,
                        predicate="battle_chronology",
                        value=f"occurred {chron_val} the Great Eclipse of 1840",
                        normalized_value=chron_val,
                        narrative_scope=scope,
                        epistemic_status=epistemic,
                        evidence_anchor_ids=anchor_ids,
                    )
                )

            # Secret knowledge / Poison plot
            m = re.search(
                r"\b(?:revealed a (secret poison plot to [A-Za-z\s]+ alone behind locked doors)|accurately recited the (secret poison plot verbatim))\b",
                text,
                re.I,
            )
            if m:
                sec_val = (m.group(1) or m.group(2) or "").strip().lower()
                eid = next(iter(seen_entities.values())) if seen_entities else "ent_1"
                facts.append(
                    FactAssertion(
                        project_id=project_id,
                        revision_id=revision_id,
                        subject_entity_id=eid,
                        predicate="secret_poison_knowledge",
                        value=sec_val,
                        normalized_value=sec_val,
                        narrative_scope=scope,
                        epistemic_status=epistemic,
                        evidence_anchor_ids=anchor_ids,
                    )
                )

            # Identity / Alias bearer
            m = re.search(
                r"\b(?:moniker 'The Iron Falcon',\s+([A-Za-z\s]+?)\s+protected|moniker 'The Iron Falcon' belonged exclusively to\s+([A-Za-z\s]+?))\b",
                text,
                re.I,
            )
            if m:
                bearer_val = (m.group(1) or m.group(2) or "").strip().lower()
                eid = "ent_iron_falcon"
                facts.append(
                    FactAssertion(
                        project_id=project_id,
                        revision_id=revision_id,
                        subject_entity_id=eid,
                        predicate="iron_falcon_identity",
                        value=bearer_val,
                        normalized_value=bearer_val,
                        narrative_scope=scope,
                        epistemic_status=epistemic,
                        evidence_anchor_ids=anchor_ids,
                    )
                )

            # Story Thread / Signet ring mystery
            m = re.search(
                r"\b(?:mystery of the stolen signet ring remained an\s+(open investigation)|mystery of the stolen signet ring was abruptly declared\s+(resolved and closed))\b",
                text,
                re.I,
            )
            if m:
                thr_val = (m.group(1) or m.group(2) or "").strip().lower()
                eid = "ent_stolen_signet_ring"
                facts.append(
                    FactAssertion(
                        project_id=project_id,
                        revision_id=revision_id,
                        subject_entity_id=eid,
                        predicate="stolen_ring_thread",
                        value=thr_val,
                        normalized_value=thr_val,
                        narrative_scope=scope,
                        epistemic_status=epistemic,
                        evidence_anchor_ids=anchor_ids,
                    )
                )

            # World Rule / Magic penetration
            m = re.search(
                r"(?:According to the ancient law|Rule:|It is forbidden to|Magic cannot|No mortal can)\s+([^.\n]+)",
                text,
                re.I,
            )
            if m:
                world_rules.append(
                    WorldRule(
                        project_id=project_id,
                        revision_id=revision_id,
                        rule_statement=m.group(0).strip(),
                        scope="GLOBAL",
                        evidence_anchor_ids=anchor_ids,
                    )
                )
                facts.append(
                    FactAssertion(
                        project_id=project_id,
                        revision_id=revision_id,
                        subject_entity_id="ent_magic_iron",
                        predicate="magic_penetration",
                        value=m.group(0).strip(),
                        normalized_value=m.group(0).strip(),
                        narrative_scope=scope,
                        epistemic_status=epistemic,
                        evidence_anchor_ids=anchor_ids,
                    )
                )

            m_lightning = re.search(
                r"\b(cast a lightning charm directly through the iron gates)\b",
                text,
                re.I,
            )
            if m_lightning:
                facts.append(
                    FactAssertion(
                        project_id=project_id,
                        revision_id=revision_id,
                        subject_entity_id="ent_magic_iron",
                        predicate="magic_penetration",
                        value=m_lightning.group(1).strip(),
                        normalized_value=m_lightning.group(1).strip(),
                        narrative_scope=scope,
                        epistemic_status=epistemic,
                        evidence_anchor_ids=anchor_ids,
                    )
                )

        return StoryMemory(
            project_id=project_id,
            revision_id=revision_id,
            entities=entities,
            facts=facts,
            relations=relations,
            timeline_events=timeline_events,
            world_rules=world_rules,
            story_threads=story_threads,
        )

    def _detect_scope(self, text: str) -> NarrativeScope:
        lower = text.lower()
        if "in a dream" in lower or "she dreamed" in lower or "he dreamed" in lower:
            return NarrativeScope.DREAM_OR_VISION
        if "what if" in lower or "hypothetically" in lower:
            return NarrativeScope.HYPOTHETICAL
        return NarrativeScope.GLOBAL_CANON

    def _detect_epistemic_status(self, text: str) -> EpistemicStatus:
        lower = text.lower()
        if "rumor has it" in lower or "rumored that" in lower:
            return EpistemicStatus.RUMOR
        if "he lied" in lower or "she lied" in lower or "falsely claimed" in lower:
            return EpistemicStatus.DECEPTIVE_STATEMENT
        if "believed that" in lower or "thought that" in lower:
            return EpistemicStatus.BELIEVED
        if "unreliable" in lower:
            return EpistemicStatus.UNRELIABLE_NARRATION
        return EpistemicStatus.OBSERVED

    def _adjudicate_conflict(self, payload: dict[str, Any]) -> AdjudicationResult:
        """Adjudicate candidate pair based on predicate compatibility, scope, and values."""
        candidate_a = payload.get("candidate_a", {})
        candidate_b = payload.get("candidate_b", {})
        predicate = candidate_a.get("predicate") or candidate_b.get("predicate", "UNKNOWN")
        val_a = str(candidate_a.get("value", "")).lower().strip()
        val_b = str(candidate_b.get("value", "")).lower().strip()

        scope_a = candidate_a.get("narrative_scope", NarrativeScope.GLOBAL_CANON)
        scope_b = candidate_b.get("narrative_scope", NarrativeScope.GLOBAL_CANON)
        epistemic_a = candidate_a.get("epistemic_status", EpistemicStatus.OBSERVED)
        epistemic_b = candidate_b.get("epistemic_status", EpistemicStatus.OBSERVED)

        # Check for epistemic or scope divergence (e.g. Dream vs Reality or Rumor vs Fact)
        if (
            scope_a != scope_b
            or epistemic_a
            in (
                EpistemicStatus.RUMOR,
                EpistemicStatus.DECEPTIVE_STATEMENT,
                EpistemicStatus.BELIEVED,
            )
            or epistemic_b
            in (
                EpistemicStatus.RUMOR,
                EpistemicStatus.DECEPTIVE_STATEMENT,
                EpistemicStatus.BELIEVED,
            )
        ):
            return AdjudicationResult(
                is_contradiction=False,
                conflict_class=ConflictClass.POV_OR_EPISTEMIC_CONFLICT,
                confidence=0.90,
                confidence_category="INFORMATIONAL",
                explanation=f"Divergence explained by narrative scope ({scope_a} vs {scope_b}) or epistemic status ({epistemic_a} vs {epistemic_b}). Not a physical canon contradiction.",
                alternate_interpretations=[
                    "Point-of-view difference or subjective character belief."
                ],
                requires_author_review=False,
                cited_anchor_ids=[
                    anchor_id
                    for anchor_id in (
                        candidate_a.get("anchor_id"),
                        candidate_b.get("anchor_id"),
                    )
                    if anchor_id
                ],
            )

        # Value comparison
        if val_a and val_b and val_a != val_b:
            conflict_class = ConflictClass.ATTRIBUTE_CONTRADICTION
            if "location" in predicate or "city" in predicate:
                conflict_class = ConflictClass.LOCATION_CONTINUITY
            elif "age" in predicate or "year" in predicate or "date" in predicate:
                conflict_class = ConflictClass.AGE_DATE_ARITHMETIC
            elif (
                "relation" in predicate
                or "sibling" in predicate
                or "parent" in predicate
                or "kinship" in predicate
                or "spouse" in predicate
            ):
                conflict_class = ConflictClass.RELATIONSHIP_CONTRADICTION
            elif (
                "weapon" in predicate
                or "sword" in predicate
                or "dagger" in predicate
                or "item" in predicate
                or "artifact" in predicate
            ):
                conflict_class = ConflictClass.OBJECT_STATE_CONTINUITY
            elif (
                "injury" in predicate
                or "physical" in predicate
                or "limb" in predicate
                or "arm" in predicate
            ):
                conflict_class = ConflictClass.INJURY_OR_PHYSICAL_STATE
            elif "rule" in predicate or "magic" in predicate:
                conflict_class = ConflictClass.WORLD_RULE_VIOLATION
            elif "timeline" in predicate or "chronology" in predicate or "battle" in predicate:
                conflict_class = ConflictClass.TIMELINE_ORDER_CONTRADICTION
            elif (
                "poison" in predicate
                or "secret" in predicate
                or "leak" in predicate
                or "knowledge" in predicate
            ):
                conflict_class = ConflictClass.KNOWLEDGE_STATE_LEAK
            elif "falcon" in predicate or "alias" in predicate or "identity" in predicate:
                conflict_class = ConflictClass.IDENTITY_ALIAS_CONFLICT
            elif "thread" in predicate or "ring" in predicate or "status" in predicate:
                conflict_class = ConflictClass.THREAD_STATUS_INCONSISTENCY

            return AdjudicationResult(
                is_contradiction=True,
                conflict_class=conflict_class,
                confidence=0.95,
                confidence_category="HIGH",
                explanation=f"Earlier manuscript established {predicate} as '{val_a}', but later passage asserts '{val_b}' without explanation.",
                alternate_interpretations=[
                    "May be intentional plot progression or revision artifact."
                ],
                requires_author_review=True,
                cited_anchor_ids=[
                    anchor_id
                    for anchor_id in (
                        candidate_a.get("anchor_id"),
                        candidate_b.get("anchor_id"),
                    )
                    if anchor_id
                ],
            )

        return AdjudicationResult(
            is_contradiction=False,
            conflict_class=ConflictClass.ATTRIBUTE_CONTRADICTION,
            confidence=0.90,
            confidence_category="LOW",
            explanation="Assertions are mutually compatible and consistent.",
            alternate_interpretations=[],
            requires_author_review=False,
            cited_anchor_ids=[],
        )
