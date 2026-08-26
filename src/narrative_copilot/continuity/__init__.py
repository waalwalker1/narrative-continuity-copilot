"""
Narrative continuity reasoning and adjudication package.
"""

from narrative_copilot.continuity.candidate_generator import CandidateGenerator
from narrative_copilot.continuity.critic import EvidenceCritic, EvidenceCriticResult
from narrative_copilot.continuity.engine import ContinuityReasoningEngine
from narrative_copilot.continuity.preconditions import PreconditionChecker
from narrative_copilot.continuity.taxonomy import TAXONOMY_DESCRIPTIONS
from narrative_copilot.continuity.validator import DeterministicOutputValidator

__all__ = [
    "TAXONOMY_DESCRIPTIONS",
    "CandidateGenerator",
    "ContinuityReasoningEngine",
    "DeterministicOutputValidator",
    "EvidenceCritic",
    "EvidenceCriticResult",
    "PreconditionChecker",
]
