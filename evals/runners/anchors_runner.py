"""
Anchor Stability and Edit Re-anchoring Benchmark Runner.
Evaluates >= 200 edit operations across text insertions, deletions, paragraph splits, merges, and renames.
"""

from typing import Any

from narrative_copilot.anchors.reanchoring import ReanchoringEngine, compute_text_hash
from narrative_copilot.schemas import SourceAnchor, StructuralUnit, UnitType

STATUSES = ["EXACT_MATCH", "REALIGNED", "TRANSFERRED_BLOCK", "INVALIDATED"]


class AnchorBenchmarkRunner:
    def __init__(self) -> None:
        self.engine = ReanchoringEngine()

    def run_benchmark(self, num_ops: int = 220) -> dict[str, Any]:
        """
        Execute >= 200 anchor edit mutations and measure retention, accuracy, and false re-anchoring
        against gold expected outcomes and target block IDs.
        """
        confusion_matrix: dict[str, dict[str, int]] = {
            exp: dict.fromkeys(STATUSES, 0) for exp in STATUSES
        }
        expected_counts: dict[str, int] = dict.fromkeys(STATUSES, 0)
        actual_counts: dict[str, int] = dict.fromkeys(STATUSES, 0)
        correct_status_counts: dict[str, int] = dict.fromkeys(STATUSES, 0)

        total_ops = 0
        correct_full_outcomes = 0
        correct_invalidated_count = 0
        false_reanchor_count = 0
        failure_cases: list[dict[str, Any]] = []

        # Run 9 mutation types across batches
        for i in range(num_ops):
            total_ops += 1
            op_type = i % 9
            block_id = f"blk_{i:04d}"
            base_text = (
                f"Paragraph {i}: Lord Arthur Vance examined the silver talisman on the stone table."
            )
            quote = "silver talisman on the stone"

            original_anchor = SourceAnchor(
                anchor_id=f"anc_{i:04d}",
                project_id="proj_anchor_bench",
                revision_id="rev_1",
                chapter_id="chap_1",
                block_id=block_id,
                char_start=base_text.find(quote),
                char_end=base_text.find(quote) + len(quote),
                text_hash=compute_text_hash(quote),
                normalized_quote=quote,
            )

            target_blocks: list[StructuralUnit] = []
            expected_status: str = "EXACT_MATCH"
            expected_target_block_id: str | None = block_id
            mutation_name: str = ""

            if op_type == 0:
                # 0. Unchanged text (Exact retention)
                mutation_name = "UNCHANGED_TEXT"
                expected_status = "EXACT_MATCH"
                expected_target_block_id = block_id
                target_blocks = [
                    StructuralUnit(
                        unit_id=block_id,
                        project_id="proj_anchor_bench",
                        revision_id="rev_2",
                        unit_type=UnitType.BLOCK,
                        text=base_text,
                    )
                ]
            elif op_type == 1:
                # 1. Text inserted BEFORE citation (shifts offset)
                mutation_name = "PREFIX_INSERTION"
                expected_status = "REALIGNED"
                expected_target_block_id = block_id
                mutated = "At early dawn, " + base_text
                target_blocks = [
                    StructuralUnit(
                        unit_id=block_id,
                        project_id="proj_anchor_bench",
                        revision_id="rev_2",
                        unit_type=UnitType.BLOCK,
                        text=mutated,
                    )
                ]
            elif op_type == 2:
                # 2. Text inserted inside block before quote (shifts offset)
                mutation_name = "MID_BLOCK_INSERTION"
                expected_status = "REALIGNED"
                expected_target_block_id = block_id
                mutated = base_text.replace("examined the", "quietly and carefully examined the")
                target_blocks = [
                    StructuralUnit(
                        unit_id=block_id,
                        project_id="proj_anchor_bench",
                        revision_id="rev_2",
                        unit_type=UnitType.BLOCK,
                        text=mutated,
                    )
                ]
            elif op_type == 3:
                # 3. Typo fix / minor edit inside quote span (fuzzy alignment)
                mutation_name = "TYPO_FUZZY_EDIT"
                expected_status = "REALIGNED"
                expected_target_block_id = block_id
                mutated = base_text.replace("talisman", "talismann")
                target_blocks = [
                    StructuralUnit(
                        unit_id=block_id,
                        project_id="proj_anchor_bench",
                        revision_id="rev_2",
                        unit_type=UnitType.BLOCK,
                        text=mutated,
                    )
                ]
            elif op_type == 4:
                # 4. Paragraph split into two blocks (quote moved to 2nd block)
                mutation_name = "PARAGRAPH_SPLIT"
                expected_status = "TRANSFERRED_BLOCK"
                expected_target_block_id = f"{block_id}_split"
                part1 = f"Paragraph {i}: Lord Arthur Vance examined the "
                part2 = "silver talisman on the stone table."
                target_blocks = [
                    StructuralUnit(
                        unit_id=block_id,
                        project_id="proj_anchor_bench",
                        revision_id="rev_2",
                        unit_type=UnitType.BLOCK,
                        text=part1,
                    ),
                    StructuralUnit(
                        unit_id=f"{block_id}_split",
                        project_id="proj_anchor_bench",
                        revision_id="rev_2",
                        unit_type=UnitType.BLOCK,
                        text=part2,
                    ),
                ]
            elif op_type == 5:
                # 5. Paragraph merged with preceding block (shifts offset)
                mutation_name = "PARAGRAPH_MERGE"
                expected_status = "REALIGNED"
                expected_target_block_id = block_id
                merged = "Previous context. " + base_text
                target_blocks = [
                    StructuralUnit(
                        unit_id=block_id,
                        project_id="proj_anchor_bench",
                        revision_id="rev_2",
                        unit_type=UnitType.BLOCK,
                        text=merged,
                    )
                ]
            elif op_type == 6:
                # 6. Entity renamed (Arthur Vance -> Marcus Thorne)
                mutation_name = "ENTITY_RENAME"
                expected_status = "REALIGNED"
                expected_target_block_id = block_id
                renamed = base_text.replace("Arthur Vance", "Marcus Thorne")
                target_blocks = [
                    StructuralUnit(
                        unit_id=block_id,
                        project_id="proj_anchor_bench",
                        revision_id="rev_2",
                        unit_type=UnitType.BLOCK,
                        text=renamed,
                    )
                ]
            elif op_type == 7:
                # 7. Chapter / block moved to new block UUID
                mutation_name = "BLOCK_UUID_MOVE"
                expected_status = "TRANSFERRED_BLOCK"
                expected_target_block_id = f"{block_id}_moved"
                target_blocks = [
                    StructuralUnit(
                        unit_id=f"{block_id}_moved",
                        project_id="proj_anchor_bench",
                        revision_id="rev_2",
                        unit_type=UnitType.BLOCK,
                        text=base_text,
                    )
                ]
            elif op_type == 8:
                # 8. Block deleted completely
                mutation_name = "BLOCK_DELETION"
                expected_status = "INVALIDATED"
                expected_target_block_id = None
                target_blocks = [
                    StructuralUnit(
                        unit_id=f"other_{i}",
                        project_id="proj_anchor_bench",
                        revision_id="rev_2",
                        unit_type=UnitType.BLOCK,
                        text="Unrelated text about market trade in the eastern port.",
                    )
                ]

            expected_counts[expected_status] += 1
            result = self.engine.reanchor(original_anchor, "rev_2", target_blocks)
            actual_status = result.status
            actual_counts[actual_status] += 1
            confusion_matrix[expected_status][actual_status] += 1

            actual_target_block_id = (
                result.updated_anchor.block_id if result.updated_anchor else None
            )

            status_correct = actual_status == expected_status
            if status_correct:
                correct_status_counts[expected_status] += 1
                if expected_status == "INVALIDATED":
                    correct_invalidated_count += 1

            if expected_status == "INVALIDATED":
                target_correct = actual_target_block_id is None
            else:
                target_correct = actual_target_block_id == expected_target_block_id

            full_outcome_correct = status_correct and target_correct
            if full_outcome_correct:
                correct_full_outcomes += 1
            else:
                failure_cases.append(
                    {
                        "op_index": i,
                        "mutation": mutation_name,
                        "expected_status": expected_status,
                        "actual_status": actual_status,
                        "expected_block": expected_target_block_id,
                        "actual_block": actual_target_block_id,
                    }
                )

            # False reanchor criteria:
            # 1. Expected INVALIDATED, but actual reanchored to unrelated text.
            # 2. Expected target block X, but actual reanchored to wrong block Y.
            is_false_reanchor = False
            if (expected_status == "INVALIDATED" and actual_status != "INVALIDATED") or (
                expected_status != "INVALIDATED"
                and actual_status != "INVALIDATED"
                and actual_target_block_id != expected_target_block_id
            ):
                is_false_reanchor = True

            if is_false_reanchor:
                false_reanchor_count += 1

        # Calculate mathematically sound per-class and aggregate metrics
        exact_match_accuracy = correct_status_counts["EXACT_MATCH"] / max(
            expected_counts["EXACT_MATCH"], 1
        )
        realignment_accuracy = correct_status_counts["REALIGNED"] / max(
            expected_counts["REALIGNED"], 1
        )
        transfer_accuracy = correct_status_counts["TRANSFERRED_BLOCK"] / max(
            expected_counts["TRANSFERRED_BLOCK"], 1
        )
        invalidation_accuracy = correct_status_counts["INVALIDATED"] / max(
            expected_counts["INVALIDATED"], 1
        )
        invalidation_precision = correct_invalidated_count / max(actual_counts["INVALIDATED"], 1)
        false_reanchor_rate = false_reanchor_count / max(total_ops, 1)
        expected_outcome_accuracy = correct_full_outcomes / max(total_ops, 1)
        retention_rate = actual_counts["EXACT_MATCH"] / max(total_ops, 1)

        # Invariant checks: all rates must be in [0.0, 1.0]
        assert 0.0 <= exact_match_accuracy <= 1.0, (
            f"exact_match_accuracy out of range: {exact_match_accuracy}"
        )
        assert 0.0 <= realignment_accuracy <= 1.0, (
            f"realignment_accuracy out of range: {realignment_accuracy}"
        )
        assert 0.0 <= transfer_accuracy <= 1.0, (
            f"transfer_accuracy out of range: {transfer_accuracy}"
        )
        assert 0.0 <= invalidation_accuracy <= 1.0, (
            f"invalidation_accuracy out of range: {invalidation_accuracy}"
        )
        assert 0.0 <= invalidation_precision <= 1.0, (
            f"invalidation_precision out of range: {invalidation_precision}"
        )
        assert 0.0 <= false_reanchor_rate <= 1.0, (
            f"false_reanchor_rate out of range: {false_reanchor_rate}"
        )
        assert 0.0 <= expected_outcome_accuracy <= 1.0, (
            f"expected_outcome_accuracy out of range: {expected_outcome_accuracy}"
        )

        return {
            "total_operations": total_ops,
            "expected_counts": expected_counts,
            "actual_counts": actual_counts,
            "confusion_matrix": confusion_matrix,
            "exact_match_accuracy": round(exact_match_accuracy, 4),
            "realignment_accuracy": round(realignment_accuracy, 4),
            "transfer_accuracy": round(transfer_accuracy, 4),
            "invalidation_accuracy": round(invalidation_accuracy, 4),
            "invalidation_precision": round(invalidation_precision, 4),
            "false_reanchors": false_reanchor_count,
            "false_reanchor_rate": round(false_reanchor_rate, 4),
            "expected_outcome_accuracy": round(expected_outcome_accuracy, 4),
            "exact_matches": actual_counts["EXACT_MATCH"],
            "realigned": actual_counts["REALIGNED"],
            "transferred_blocks": actual_counts["TRANSFERRED_BLOCK"],
            "invalidated": actual_counts["INVALIDATED"],
            "retention_rate": round(retention_rate, 4),
            "failure_cases_count": len(failure_cases),
        }
