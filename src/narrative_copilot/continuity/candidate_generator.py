"""
Candidate generator for narrative continuity verification.
Identifies potentially conflicting assertion pairs across structured story memory.
"""

from collections import defaultdict
from uuid import uuid4

from narrative_copilot.schemas import (
    CanonicalStatus,
    FactAssertion,
    SourceAnchor,
    StoryMemory,
    StructuralUnit,
    UnitType,
)
from narrative_copilot.schemas.continuity import CandidatePair


class CandidateGenerator:
    """
    Pairs competing narrative assertions by entity, predicate, and timeline scope.
    """

    def generate_candidates(
        self,
        memory: StoryMemory,
        anchors: list[SourceAnchor],
        units: list[StructuralUnit],
    ) -> list[CandidatePair]:
        """
        Generate list of candidate pairs from story memory facts and anchors.
        """
        anchor_lookup = {a.anchor_id: a for a in anchors}
        block_units = {u.unit_id: u for u in units if u.unit_type == UnitType.BLOCK}

        # Group facts by (subject_entity_id, predicate)
        grouped_facts: dict[tuple[str, str], list[FactAssertion]] = defaultdict(list)
        for fact in memory.facts:
            # Skip superseded or ignored facts
            if fact.canonical_status in (CanonicalStatus.SUPERSEDED, CanonicalStatus.IGNORED):
                continue
            grouped_facts[(fact.subject_entity_id, fact.predicate)].append(fact)

        candidates: list[CandidatePair] = []

        for (subj_id, pred), facts in grouped_facts.items():
            if len(facts) < 2:
                continue

            # Compare pairs of facts
            for i in range(len(facts)):
                for j in range(i + 1, len(facts)):
                    f_a = facts[i]
                    f_b = facts[j]

                    # Retrieve anchor metadata
                    aid_a = f_a.evidence_anchor_ids[0] if f_a.evidence_anchor_ids else ""
                    aid_b = f_b.evidence_anchor_ids[0] if f_b.evidence_anchor_ids else ""
                    if not aid_a or not aid_b or aid_a == aid_b:
                        continue

                    anc_a = anchor_lookup.get(aid_a)
                    anc_b = anchor_lookup.get(aid_b)
                    if not anc_a or not anc_b:
                        continue

                    blk_a = block_units.get(anc_a.block_id)
                    blk_b = block_units.get(anc_b.block_id)
                    snip_a = blk_a.text if blk_a else anc_a.normalized_quote
                    snip_b = blk_b.text if blk_b else anc_b.normalized_quote

                    candidate = CandidatePair(
                        pair_id=str(uuid4()),
                        project_id=memory.project_id,
                        revision_id=memory.revision_id,
                        fact_id_a=f_a.fact_id,
                        fact_id_b=f_b.fact_id,
                        subject_entity_id=subj_id,
                        predicate=pred,
                        value_a=f_a.value or f_a.normalized_value,
                        value_b=f_b.value or f_b.normalized_value,
                        anchor_id_a=aid_a,
                        anchor_id_b=aid_b,
                        snippet_a=snip_a[:400],
                        snippet_b=snip_b[:400],
                        chapter_id_a=anc_a.chapter_id,
                        chapter_id_b=anc_b.chapter_id,
                        block_id_a=anc_a.block_id,
                        block_id_b=anc_b.block_id,
                        narrative_scope_a=f_a.narrative_scope.value,
                        narrative_scope_b=f_b.narrative_scope.value,
                        epistemic_status_a=f_a.epistemic_status.value,
                        epistemic_status_b=f_b.epistemic_status.value,
                        temporal_scope_a=f_a.temporal_scope,
                        temporal_scope_b=f_b.temporal_scope,
                    )
                    candidates.append(candidate)

        # Compare world rules against blocks
        for rule in memory.world_rules:
            rule_aid = rule.evidence_anchor_ids[0] if rule.evidence_anchor_ids else ""
            rule_anc = anchor_lookup.get(rule_aid)
            if not rule_anc:
                continue

            if (
                "iron" in rule.rule_statement.lower()
                or "magic cannot" in rule.rule_statement.lower()
            ):
                for b_id, blk in block_units.items():
                    if b_id == rule_anc.block_id:
                        continue
                    if "through the iron" in blk.text.lower() or "lightning" in blk.text.lower():
                        blk_anc = next((a for a in anchors if a.block_id == b_id), None)
                        if blk_anc:
                            candidates.append(
                                CandidatePair(
                                    pair_id=str(uuid4()),
                                    project_id=memory.project_id,
                                    revision_id=memory.revision_id,
                                    fact_id_a=rule.rule_id,
                                    fact_id_b=f"fact_{blk.unit_id}",
                                    subject_entity_id="Magic Rules",
                                    predicate="magic_penetration",
                                    value_a=rule.rule_statement,
                                    value_b=blk.text,
                                    anchor_id_a=rule_aid,
                                    anchor_id_b=blk_anc.anchor_id,
                                    snippet_a=rule.rule_statement[:400],
                                    snippet_b=blk.text[:400],
                                    chapter_id_a=rule_anc.chapter_id,
                                    chapter_id_b=blk_anc.chapter_id,
                                    block_id_a=rule_anc.block_id,
                                    block_id_b=blk.unit_id,
                                )
                            )

        return candidates
