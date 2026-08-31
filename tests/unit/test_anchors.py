"""
Unit tests for stable provenance and re-anchoring engine.
"""

from narrative_copilot.anchors.reanchoring import ReanchoringEngine, compute_text_hash
from narrative_copilot.schemas import SourceAnchor, StructuralUnit, UnitType


def test_reanchoring_exact_match() -> None:
    engine = ReanchoringEngine()
    text = "Arthur had blue eyes."
    anchor = SourceAnchor(
        anchor_id="anc_1",
        project_id="p1",
        revision_id="rev_1",
        chapter_id="c1",
        block_id="blk_1",
        char_start=0,
        char_end=len(text),
        text_hash=compute_text_hash(text),
        normalized_quote=text,
    )

    blocks = [
        StructuralUnit(
            unit_id="blk_1",
            project_id="p1",
            revision_id="rev_2",
            unit_type=UnitType.BLOCK,
            text=text,
        )
    ]

    result = engine.reanchor(anchor, "rev_2", blocks)
    assert result.status == "EXACT_MATCH"
    assert result.confidence == 1.0
    assert result.updated_anchor is not None
    assert result.updated_anchor.revision_id == "rev_2"


def test_reanchoring_prefix_insertion_realigned() -> None:
    engine = ReanchoringEngine()
    quote = "Arthur had blue eyes."
    anchor = SourceAnchor(
        anchor_id="anc_1",
        project_id="p1",
        revision_id="rev_1",
        chapter_id="c1",
        block_id="blk_1",
        char_start=0,
        char_end=len(quote),
        text_hash=compute_text_hash(quote),
        normalized_quote=quote,
    )

    mutated_text = "Early in the morning, Arthur had blue eyes."
    blocks = [
        StructuralUnit(
            unit_id="blk_1",
            project_id="p1",
            revision_id="rev_2",
            unit_type=UnitType.BLOCK,
            text=mutated_text,
        )
    ]

    result = engine.reanchor(anchor, "rev_2", blocks)
    assert result.status == "REALIGNED"
    assert result.confidence >= 0.95
    assert result.updated_anchor is not None
    assert result.updated_anchor.char_start == mutated_text.find(quote)


def test_reanchoring_deleted_block_invalidated() -> None:
    engine = ReanchoringEngine()
    quote = "Arthur had blue eyes."
    anchor = SourceAnchor(
        anchor_id="anc_1",
        project_id="p1",
        revision_id="rev_1",
        chapter_id="c1",
        block_id="blk_1",
        char_start=0,
        char_end=len(quote),
        text_hash=compute_text_hash(quote),
        normalized_quote=quote,
    )

    blocks = [
        StructuralUnit(
            unit_id="blk_other",
            project_id="p1",
            revision_id="rev_2",
            unit_type=UnitType.BLOCK,
            text="Completely different paragraph about the harvest festival.",
        )
    ]

    result = engine.reanchor(anchor, "rev_2", blocks)
    assert result.status == "INVALIDATED"
    assert result.updated_anchor is None


def test_reanchoring_split_transferred_block() -> None:
    engine = ReanchoringEngine()
    quote = "silver talisman on the stone table"
    anchor = SourceAnchor(
        anchor_id="anc_split",
        project_id="p1",
        revision_id="rev_1",
        chapter_id="c1",
        block_id="blk_1",
        char_start=20,
        char_end=20 + len(quote),
        text_hash=compute_text_hash(quote),
        normalized_quote=quote,
    )

    blocks = [
        StructuralUnit(
            unit_id="blk_1",
            project_id="p1",
            revision_id="rev_2",
            unit_type=UnitType.BLOCK,
            text="Lord Arthur Vance examined the ",
        ),
        StructuralUnit(
            unit_id="blk_1_split",
            project_id="p1",
            revision_id="rev_2",
            unit_type=UnitType.BLOCK,
            text="silver talisman on the stone table in the vault.",
        ),
    ]

    result = engine.reanchor(anchor, "rev_2", blocks)
    assert result.status == "TRANSFERRED_BLOCK"
    assert result.updated_anchor is not None
    assert result.updated_anchor.block_id == "blk_1_split"


def test_anchor_benchmark_runner_mathematics_bounds() -> None:
    from evals.runners.anchors_runner import AnchorBenchmarkRunner

    runner = AnchorBenchmarkRunner()
    results = runner.run_benchmark(num_ops=220)

    # Invariant: all rates and accuracies must be in [0.0, 1.0]
    for key in [
        "exact_match_accuracy",
        "realignment_accuracy",
        "transfer_accuracy",
        "invalidation_accuracy",
        "invalidation_precision",
        "false_reanchor_rate",
        "expected_outcome_accuracy",
        "retention_rate",
    ]:
        val = results[key]
        assert 0.0 <= val <= 1.0, f"Metric '{key}' has invalid value {val}"

    # Verify confusion matrix sums
    cm = results["confusion_matrix"]
    total_in_cm = sum(sum(row.values()) for row in cm.values())
    assert total_in_cm == results["total_operations"] == 220
    assert results["false_reanchor_rate"] == 0.0
