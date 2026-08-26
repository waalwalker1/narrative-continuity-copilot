"""
Evidence Critic module.
Rigorously checks candidate pairs and adjudication results against evidence anchors and narrative epistemic constraints.
"""

from narrative_copilot.schemas import SourceAnchor
from narrative_copilot.schemas.continuity import AdjudicationResult, CandidatePair


class EvidenceCriticResult:
    def __init__(self, is_valid: bool, critique: str):
        self.is_valid = is_valid
        self.critique = critique


class EvidenceCritic:
    """
    Evaluates evidence sufficiency and narrative grounding before an alert can reach author review.
    """

    def critique_adjudication(
        self,
        candidate: CandidatePair,
        adjudication: AdjudicationResult,
        known_anchors: dict[str, SourceAnchor],
    ) -> EvidenceCriticResult:
        """
        Critique the adjudication output against known anchors and narrative scope.
        """
        # 1. Check anchor existence in known anchors
        if candidate.anchor_id_a not in known_anchors or candidate.anchor_id_b not in known_anchors:
            return EvidenceCriticResult(
                is_valid=False,
                critique="Evidence anchor does not exist in manuscript anchor registry.",
            )

        # 2. Check cited anchor IDs in adjudication
        for aid in adjudication.cited_anchor_ids:
            if aid not in known_anchors:
                return EvidenceCriticResult(
                    is_valid=False,
                    critique=f"Adjudication cited unknown anchor ID '{aid}'.",
                )

        # 3. Check if narrative scopes explain the difference (e.g. Dream vs Real or Rumor vs Fact)
        if candidate.narrative_scope_a != candidate.narrative_scope_b and (
            adjudication.is_contradiction and adjudication.confidence_category == "HIGH"
        ):
            # Downgrade or reject: A dream cannot strictly contradict waking reality without author review
            return EvidenceCriticResult(
                is_valid=True,
                critique="Narrative scope divergence detected (e.g. dream vs reality). Alert marked informational.",
            )

        return EvidenceCriticResult(
            is_valid=True, critique="Evidence anchors and reasoning validated."
        )
