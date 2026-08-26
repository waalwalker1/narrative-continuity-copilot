"""
Deterministic precondition engine for candidate continuity pairs.
Filters out incompatible, superseded, or author-suppressed pairs before AI adjudication.
"""

from narrative_copilot.schemas.continuity import CandidatePair, DeterministicPreconditionResult


class PreconditionChecker:
    """
    Evaluates deterministic criteria before passing candidate fact pairs to LLM adjudicators.
    """

    def check_preconditions(
        self,
        candidate: CandidatePair,
        suppressed_alert_pair_keys: set[str] | None = None,
    ) -> DeterministicPreconditionResult:
        """
        Verify that candidate pair satisfies all strict preconditions.
        """
        # 1. Non-empty subject and predicate
        if not candidate.subject_entity_id:
            return DeterministicPreconditionResult(
                passed=False, rejection_reason="Missing subject entity ID."
            )

        if not candidate.predicate:
            return DeterministicPreconditionResult(
                passed=False, rejection_reason="Missing predicate."
            )

        # 2. Both evidence anchors must exist
        if not candidate.anchor_id_a or not candidate.anchor_id_b:
            return DeterministicPreconditionResult(
                passed=False, rejection_reason="Candidate pair missing evidence anchor IDs."
            )

        # 3. Same anchor self-comparison rejected
        if candidate.anchor_id_a == candidate.anchor_id_b:
            return DeterministicPreconditionResult(
                passed=False, rejection_reason="Candidate pair references the same anchor ID."
            )

        # 4. Check author suppression set
        pair_key = f"{candidate.fact_id_a}:{candidate.fact_id_b}"
        pair_key_rev = f"{candidate.fact_id_b}:{candidate.fact_id_a}"
        if suppressed_alert_pair_keys and (
            pair_key in suppressed_alert_pair_keys or pair_key_rev in suppressed_alert_pair_keys
        ):
            return DeterministicPreconditionResult(
                passed=False, rejection_reason="Pair suppressed by prior author decision."
            )

        # 5. Passed all preconditions
        return DeterministicPreconditionResult(passed=True, rejection_reason=None)
