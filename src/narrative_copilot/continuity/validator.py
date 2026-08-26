"""
Deterministic final validator for continuity alerts.
Rejects any output with unknown citations, missing anchors, or invalid classification.
"""

from narrative_copilot.schemas import (
    CanonicalStatus,
    ContinuityAlert,
    EvidenceSnippet,
    SourceAnchor,
)
from narrative_copilot.schemas.continuity import AdjudicationResult, CandidatePair


class DeterministicOutputValidator:
    """
    Final deterministic gate for ContinuityAlert creation.
    """

    def validate_and_build_alert(
        self,
        candidate: CandidatePair,
        adjudication: AdjudicationResult,
        known_anchors: dict[str, SourceAnchor],
    ) -> ContinuityAlert | None:
        """
        Validate adjudication and assemble a strictly grounded ContinuityAlert.
        Returns None if verification fails.
        """
        if not adjudication.is_contradiction:
            return None

        anc_a = known_anchors.get(candidate.anchor_id_a)
        anc_b = known_anchors.get(candidate.anchor_id_b)

        if not anc_a or not anc_b:
            return None

        # Assemble verified evidence snippets
        ev_a = EvidenceSnippet(
            anchor_id=anc_a.anchor_id,
            chapter_id=anc_a.chapter_id,
            scene_id=anc_a.scene_id,
            block_id=anc_a.block_id,
            char_start=anc_a.char_start,
            char_end=anc_a.char_end,
            text_snippet=anc_a.normalized_quote,
            revision_id=anc_a.revision_id,
        )

        ev_b = EvidenceSnippet(
            anchor_id=anc_b.anchor_id,
            chapter_id=anc_b.chapter_id,
            scene_id=anc_b.scene_id,
            block_id=anc_b.block_id,
            char_start=anc_b.char_start,
            char_end=anc_b.char_end,
            text_snippet=anc_b.normalized_quote,
            revision_id=anc_b.revision_id,
        )

        return ContinuityAlert(
            project_id=candidate.project_id,
            revision_id=candidate.revision_id,
            conflict_class=adjudication.conflict_class,
            confidence=adjudication.confidence,
            confidence_category=adjudication.confidence_category,
            explanation=adjudication.explanation,
            alternate_interpretations=adjudication.alternate_interpretations,
            evidence_a=ev_a,
            evidence_b=ev_b,
            chapter_location=f"Chapter {anc_b.chapter_id}",
            requires_author_review=adjudication.requires_author_review,
            canonical_status=CanonicalStatus.PROPOSED,
            suppressed=False,
        )
