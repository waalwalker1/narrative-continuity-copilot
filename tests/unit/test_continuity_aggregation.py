"""
Test continuity evaluation global aggregation and extra unmatched alert accumulation.
"""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from evals.runners.continuity_runner import ContinuityEvaluator
from narrative_copilot.schemas import ConflictClass, ContinuityAlert, EvidenceSnippet


@pytest.mark.asyncio
async def test_extra_unmatched_alerts_global_accumulator(tmp_path: pytest.TempPathFactory) -> None:
    """
    Assert that extra_unmatched_alerts accumulates globally across multiple packs
    and directly impacts the precision denominator.
    """
    mock_packs = [
        {
            "story_id": "pack_1",
            "title": "Story Pack 1",
            "split": "held_out",
            "chapters": [
                {"chapter_number": 1, "title": "Chap 1", "text": "Lord Arthur had blue eyes."}
            ],
            "benchmark_cases": [
                {
                    "case_id": "case_1_1",
                    "conflict_class": ConflictClass.ATTRIBUTE_CONTRADICTION.value,
                    "expected_is_contradiction": True,
                    "evidence_a_text": "blue eyes",
                    "evidence_b_text": "blue eyes",
                }
            ],
        },
        {
            "story_id": "pack_2",
            "title": "Story Pack 2",
            "split": "held_out",
            "chapters": [
                {"chapter_number": 1, "title": "Chap 1", "text": "Lady Elena rode a white mare."}
            ],
            "benchmark_cases": [
                {
                    "case_id": "case_2_1",
                    "conflict_class": ConflictClass.ATTRIBUTE_CONTRADICTION.value,
                    "expected_is_contradiction": True,
                    "evidence_a_text": "white mare",
                    "evidence_b_text": "white mare",
                }
            ],
        },
    ]

    evaluator = ContinuityEvaluator(Path(str(tmp_path)))

    # Create dummy alerts for each pack: 1 matching alert + 1 spurious extra alert
    def make_alerts(aid_1: str, aid_2: str, extra_aid: str) -> list[ContinuityAlert]:
        return [
            ContinuityAlert(
                alert_id="alert_match",
                project_id="p1",
                revision_id="r1",
                conflict_class=ConflictClass.ATTRIBUTE_CONTRADICTION,
                confidence=0.95,
                confidence_category="HIGH",
                explanation="Matching gold alert",
                evidence_a=EvidenceSnippet(
                    anchor_id=aid_1,
                    chapter_id="c1",
                    block_id="b1",
                    char_start=0,
                    char_end=10,
                    text_snippet="quote 1",
                    revision_id="r1",
                ),
                evidence_b=EvidenceSnippet(
                    anchor_id=aid_2,
                    chapter_id="c1",
                    block_id="b2",
                    char_start=0,
                    char_end=10,
                    text_snippet="quote 2",
                    revision_id="r1",
                ),
            ),
            ContinuityAlert(
                alert_id="alert_extra",
                project_id="p1",
                revision_id="r1",
                conflict_class=ConflictClass.LOCATION_CONTINUITY,
                confidence=0.90,
                confidence_category="HIGH",
                explanation="Spurious extra unmatched alert",
                evidence_a=EvidenceSnippet(
                    anchor_id=extra_aid,
                    chapter_id="c1",
                    block_id="b3",
                    char_start=0,
                    char_end=10,
                    text_snippet="extra quote 1",
                    revision_id="r1",
                ),
                evidence_b=EvidenceSnippet(
                    anchor_id=extra_aid,
                    chapter_id="c1",
                    block_id="b4",
                    char_start=0,
                    char_end=10,
                    text_snippet="extra quote 2",
                    revision_id="r1",
                ),
            ),
        ]

    with patch("json.load", return_value=mock_packs), patch("builtins.open"):

        async def mock_review(
            memory: object, anchors: list[object], units: list[object]
        ) -> list[ContinuityAlert]:
            aids = [getattr(a, "anchor_id", "") for a in anchors] if anchors else ["a1", "a2"]
            aid1 = aids[0] if aids else "a1"
            aid2 = aids[1] if len(aids) > 1 else aid1
            return make_alerts(aid1, aid2, aid1)

        evaluator.continuity_engine.review_continuity = AsyncMock(side_effect=mock_review)
        results = await evaluator.run_evaluation()

        # Each of the 2 packs emitted 1 extra alert -> total 2
        assert results["extra_unmatched_alerts"] == 2
        assert results["true_positives"] == 2
        assert results["false_positives"] == 0
        # Precision denominator = TP (2) + FP_gold (0) + extra_unmatched (2) = 4
        # Precision = 2 / 4 = 0.50
        assert results["precision"] == 0.5
        assert len(results["class_breakdown"]) == 12
