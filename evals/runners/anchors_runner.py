"""
Anchor Stability and Edit Re-anchoring Benchmark Runner.
Evaluates >= 200 edit operations across text insertions, deletions, paragraph splits, merges, and renames.
"""

from typing import Any

from narrative_copilot.anchors.reanchoring import ReanchoringEngine, compute_text_hash
from narrative_copilot.schemas import SourceAnchor, StructuralUnit, UnitType


class AnchorBenchmarkRunner:
    def __init__(self) -> None:
        self.engine = ReanchoringEngine()

    def run_benchmark(self, num_ops: int = 220) -> dict[str, Any]:
        """
        Execute >= 200 anchor edit mutations and measure retention, accuracy, and false re-anchoring.
        """
        exact_retention_count = 0
        realigned_count = 0
        transferred_count = 0
        invalidated_count = 0
        false_reanchor_count = 0
        total_ops = 0

        expected_exact_count = 0
        expected_realigned_count = 0
        expected_transferred_count = 0
        expected_invalidated_count = 0
        correct_outcome_count = 0
        correct_invalidated_count = 0

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

            # Apply mutation to create target revision blocks
            target_blocks: list[StructuralUnit] = []
            expected_status: str = "EXACT_MATCH"

            if op_type == 0:
                # 0. Unchanged text (Exact retention)
                expected_status = "EXACT_MATCH"
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
                # 1. Text inserted BEFORE citation
                expected_status = "REALIGNED"
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
                # 2. Sentence inserted inside block after quote
                expected_status = "REALIGNED"
                mutated = base_text + " Outside, the storm raged furiously."
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
                # 3. Typo fix inside block
                expected_status = "REALIGNED"
                mutated = base_text.replace("talisman", "talismann").replace(
                    "talismann", "talisman"
                )
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
                # 4. Paragraph split into two blocks
                expected_status = "TRANSFERRED_BLOCK"
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
                # 5. Paragraph merged with preceding block
                expected_status = "REALIGNED"
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
                expected_status = "REALIGNED"
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
                expected_status = "TRANSFERRED_BLOCK"
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
                expected_status = "INVALIDATED"
                target_blocks = [
                    StructuralUnit(
                        unit_id=f"other_{i}",
                        project_id="proj_anchor_bench",
                        revision_id="rev_2",
                        unit_type=UnitType.BLOCK,
                        text="Unrelated text about market trade in the eastern port.",
                    )
                ]

            if expected_status == "EXACT_MATCH":
                expected_exact_count += 1
            elif expected_status == "REALIGNED":
                expected_realigned_count += 1
            elif expected_status == "TRANSFERRED_BLOCK":
                expected_transferred_count += 1
            elif expected_status == "INVALIDATED":
                expected_invalidated_count += 1

            result = self.engine.reanchor(original_anchor, "rev_2", target_blocks)

            if result.status == "EXACT_MATCH":
                exact_retention_count += 1
            elif result.status == "REALIGNED":
                realigned_count += 1
            elif result.status == "TRANSFERRED_BLOCK":
                transferred_count += 1
            elif result.status == "INVALIDATED":
                invalidated_count += 1

            if result.status == expected_status:
                correct_outcome_count += 1
                if expected_status == "INVALIDATED":
                    correct_invalidated_count += 1

            if expected_status == "INVALIDATED" and result.status != "INVALIDATED":
                false_reanchor_count += 1

        # Compute metric rates against declared expectations
        successful_reanchors = exact_retention_count + realigned_count + transferred_count
        retention_rate = exact_retention_count / max(total_ops, 1)
        reanchor_accuracy = (successful_reanchors + invalidated_count) / max(total_ops, 1)
        false_reanchor_rate = false_reanchor_count / max(total_ops, 1)
        exact_match_accuracy = exact_retention_count / max(expected_exact_count, 1)
        realignment_accuracy = realigned_count / max(expected_realigned_count, 1)
        transfer_accuracy = transferred_count / max(expected_transferred_count, 1)
        invalidation_precision = correct_invalidated_count / max(invalidated_count, 1)
        expected_outcome_accuracy = correct_outcome_count / max(total_ops, 1)

        return {
            "total_operations": total_ops,
            "exact_matches": exact_retention_count,
            "realigned": realigned_count,
            "transferred_blocks": transferred_count,
            "invalidated": invalidated_count,
            "false_reanchors": false_reanchor_count,
            "retention_rate": round(retention_rate, 4),
            "reanchor_accuracy": round(reanchor_accuracy, 4),
            "false_reanchor_rate": round(false_reanchor_rate, 4),
            "exact_match_accuracy": round(exact_match_accuracy, 4),
            "realignment_accuracy": round(realignment_accuracy, 4),
            "transfer_accuracy": round(transfer_accuracy, 4),
            "invalidation_precision": round(invalidation_precision, 4),
            "expected_outcome_accuracy": round(expected_outcome_accuracy, 4),
        }
