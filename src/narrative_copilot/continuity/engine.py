"""
Continuity Reasoning Engine orchestrator.
Executes the candidate -> precondition -> LLM adjudication -> critic -> validator pipeline.
Supports explicit ContinuityEngineConfig for ablation experiments and runtime tuning.
"""

from dataclasses import dataclass
from typing import Any

from narrative_copilot.continuity.candidate_generator import CandidateGenerator
from narrative_copilot.continuity.critic import EvidenceCritic
from narrative_copilot.continuity.preconditions import PreconditionChecker
from narrative_copilot.continuity.validator import DeterministicOutputValidator
from narrative_copilot.llm.provider import StructuredLLMProvider
from narrative_copilot.schemas import (
    ContinuityAlert,
    EvidenceSnippet,
    SourceAnchor,
    StoryMemory,
    StructuralUnit,
)
from narrative_copilot.schemas.continuity import AdjudicationResult


@dataclass
class ContinuityEngineConfig:
    """Explicit configuration toggles for the continuity reasoning pipeline."""

    enable_preconditions: bool = True
    enable_critic: bool = True
    enable_validator: bool = True
    enable_temporal_scoping: bool = True
    enable_epistemic_scoping: bool = True
    enable_author_rules: bool = True


class ContinuityReasoningEngine:
    """
    End-to-end continuity review pipeline.
    """

    def __init__(
        self,
        llm_provider: StructuredLLMProvider,
        config: ContinuityEngineConfig | None = None,
        precondition_checker: PreconditionChecker | None = None,
        candidate_generator: CandidateGenerator | None = None,
        critic: EvidenceCritic | None = None,
        validator: DeterministicOutputValidator | None = None,
    ) -> None:
        self.llm_provider = llm_provider
        self.config = config or ContinuityEngineConfig()
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
            # 2. Deterministic preconditions (if enabled)
            if self.config.enable_preconditions:
                pre_res = self.precondition_checker.check_preconditions(
                    candidate=candidate,
                    suppressed_alert_pair_keys=suppressed_alert_keys
                    if self.config.enable_author_rules
                    else None,
                )
                if not pre_res.passed:
                    continue

            # 3. LLM structured adjudication
            payload: dict[str, Any] = {
                "candidate_a": {
                    "predicate": candidate.predicate,
                    "value": candidate.value_a,
                    "narrative_scope": candidate.narrative_scope_a
                    if self.config.enable_epistemic_scoping
                    else "GLOBAL_CANON",
                    "epistemic_status": candidate.epistemic_status_a
                    if self.config.enable_epistemic_scoping
                    else "OBSERVED",
                    "anchor_id": candidate.anchor_id_a,
                    "snippet": candidate.snippet_a,
                },
                "candidate_b": {
                    "predicate": candidate.predicate,
                    "value": candidate.value_b,
                    "narrative_scope": candidate.narrative_scope_b
                    if self.config.enable_epistemic_scoping
                    else "GLOBAL_CANON",
                    "epistemic_status": candidate.epistemic_status_b
                    if self.config.enable_epistemic_scoping
                    else "OBSERVED",
                    "anchor_id": candidate.anchor_id_b,
                    "snippet": candidate.snippet_b,
                },
            }

            adjudication = await self.llm_provider.generate_structured(
                system_instruction=system_instruction,
                evidence_payload=payload,
                response_model=AdjudicationResult,
            )

            # 4. Evidence Critic (if enabled)
            if self.config.enable_critic:
                critic_res = self.critic.critique_adjudication(
                    candidate=candidate,
                    adjudication=adjudication,
                    known_anchors=known_anchors,
                )
                if not critic_res.is_valid:
                    continue

            # 5. Final Deterministic Validation (if enabled)
            if self.config.enable_validator:
                alert = self.validator.validate_and_build_alert(
                    candidate=candidate,
                    adjudication=adjudication,
                    known_anchors=known_anchors,
                )
                if alert is not None:
                    alerts.append(alert)
            elif (
                adjudication.is_contradiction
                and candidate.anchor_id_a in known_anchors
                and candidate.anchor_id_b in known_anchors
            ):
                anc_a = known_anchors[candidate.anchor_id_a]
                anc_b = known_anchors[candidate.anchor_id_b]
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
                alert = ContinuityAlert(
                    project_id=candidate.project_id,
                    revision_id=candidate.revision_id,
                    conflict_class=adjudication.conflict_class,
                    confidence=adjudication.confidence,
                    confidence_category=adjudication.confidence_category,
                    explanation=adjudication.explanation,
                    alternate_interpretations=adjudication.alternate_interpretations,
                    evidence_a=ev_a,
                    evidence_b=ev_b,
                )
                alerts.append(alert)

        return alerts
