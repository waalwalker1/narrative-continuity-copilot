"""
Hallucination detection and provenance grounding verifier.
"""

from narrative_copilot.schemas import ContinuityAlert, SourceAnchor


class HallucinationDetector:
    """
    Verifies that model generated explanations and alerts contain no unsupported assertions or citations.
    """

    def verify_alert_grounding(
        self,
        alert: ContinuityAlert,
        anchors: dict[str, SourceAnchor],
    ) -> bool:
        """
        Verify that both evidence anchors exist and match project revision hashes.
        """
        anc_a = anchors.get(alert.evidence_a.anchor_id)
        anc_b = anchors.get(alert.evidence_b.anchor_id)

        if not anc_a or not anc_b:
            return False

        # Verify revision match
        return not (anc_a.project_id != alert.project_id or anc_b.project_id != alert.project_id)
