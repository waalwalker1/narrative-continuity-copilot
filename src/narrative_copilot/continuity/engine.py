"""
Continuity Reasoning Engine orchestrator.
Executes the candidate -> precondition -> LLM adjudication -> critic -> validator pipeline.
"""

from narrative_copilot.continuity.candidate_generator import CandidateGenerator
from narrative_copilot.continuity.critic import EvidenceCritic
from narrative_copilot.continuity.preconditions import PreconditionChecker
from narrative_copilot.continuity.validator import DeterministicOutputValidator
from narrative_copilot.llm.provider import StructuredLLMProvider
from narrative_copilot.schemas import ContinuityAlert, SourceAnchor, StoryMemory, StructuralUnit
from narrative_copilot.schemas.continuity import AdjudicationResult


class ContinuityReasoningEngine:
    """
    End-to-end continuity review pipeline.
    """

    def __init__(
        self,
        llm_provider: StructuredLLMProvider,
        precondition_checker: PreconditionChecker | None = None,
        candidate_generator: CandidateGenerator | None = None,
        critic: EvidenceCritic | None = None,
        validator: DeterministicOutputValidator | None = None,
    ) -> None:
        self.llm_provider = llm_provider
        self.precondition_checker = precondition_checker or PreconditionChecker()
        self.candidate_generator = candidate_generator or CandidateGenerator()
        self.critic = critic or EvidenceCritic()
        self.validator = validator or DeterministicOutputValidator()

    async def review_continuity(
        self,
        memory: StoryMemory,
        anchors: list[SourceAnchor],
        units: list[StructuralUnit],
        suppressed_alert_keys: set[str] | None = None,
    ) -> list[ContinuityAlert]:
        """
        Run end-to-end continuity review over story memory and manuscript anchors.
        """
        known_anchors = {a.anchor_id: a for a in anchors}

        # 1. Generate candidate fact pairs
        candidates = self.candidate_generator.generate_candidates(memory, anchors, units)
        alerts: list[ContinuityAlert] = []

        system_instruction = (
            "You are an evidence-grounded narrative continuity adjudicator. "
            "Given two manuscript statements, determine if they represent a genuine canon contradiction "
            "or are explained by differing point-of-view, rumors, character deception, dreams, or timing. "
            "You must strictly cite only the provided anchor IDs."
        )

        for candidate in candidates:
            # 2. Deterministic preconditions
            pre_res = self.precondition_checker.check_preconditions(
                candidate=candidate,
                suppressed_alert_pair_keys=suppressed_alert_keys,
            )
            if not pre_res.passed:
                continue

            # 3. LLM structured adjudication
            payload = {
                "candidate_a": {
                    "predicate": candidate.predicate,
                    "value": candidate.value_a,
                    "narrative_scope": candidate.narrative_scope_a,
                    "epistemic_status": candidate.epistemic_status_a,
                    "anchor_id": candidate.anchor_id_a,
                    "snippet": candidate.snippet_a,
                },
                "candidate_b": {
                    "predicate": candidate.predicate,
                    "value": candidate.value_b,
                    "narrative_scope": candidate.narrative_scope_b,
                    "epistemic_status": candidate.epistemic_status_b,
                    "anchor_id": candidate.anchor_id_b,
                    "snippet": candidate.snippet_b,
                },
            }

            adjudication = await self.llm_provider.generate_structured(
                system_instruction=system_instruction,
                evidence_payload=payload,
                response_model=AdjudicationResult,
            )

            # 4. Evidence Critic
            critic_res = self.critic.critique_adjudication(
                candidate=candidate,
                adjudication=adjudication,
                known_anchors=known_anchors,
            )
            if not critic_res.is_valid:
                continue

            # 5. Final Deterministic Validation
            alert = self.validator.validate_and_build_alert(
                candidate=candidate,
                adjudication=adjudication,
                known_anchors=known_anchors,
            )
            if alert is not None:
                alerts.append(alert)

        return alerts
