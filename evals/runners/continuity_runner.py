"""
End-to-end Continuity Evaluation Runner.
Evaluates accuracy, per-class metrics, intentional ambiguity handling, citation validity, and failure cases.
Strictly evaluates over held-out story packs with exact gold-anchor pair matching and 1-to-1 alert consumption.
"""

import json
from pathlib import Path
from typing import Any

from narrative_copilot.continuity.engine import ContinuityReasoningEngine
from narrative_copilot.ingestion.importer import ManuscriptImporter
from narrative_copilot.llm.deterministic_fixture import DeterministicFixtureLLMProvider
from narrative_copilot.memory.extractor import StoryMemoryExtractor


class ContinuityEvaluator:
    def __init__(self, fixtures_path: Path, held_out_only: bool = True) -> None:
        self.fixtures_path = fixtures_path
        self.held_out_only = held_out_only
        self.llm_provider = DeterministicFixtureLLMProvider()
        self.memory_extractor = StoryMemoryExtractor(self.llm_provider)
        self.continuity_engine = ContinuityReasoningEngine(self.llm_provider)
        self.importer = ManuscriptImporter()

    async def run_evaluation(self) -> dict[str, Any]:
        packs_file = self.fixtures_path / "story_packs.json"
        with open(packs_file, encoding="utf-8") as f:
            packs = json.load(f)

        if self.held_out_only:
            packs = [p for p in packs if p.get("split") == "held_out"]

        true_positives = 0
        false_positives = 0
        true_negatives = 0
        false_negatives = 0

        intentional_ambiguity_total = 0
        intentional_ambiguity_fps = 0

        citation_valid_count = 0
        total_alerts_generated = 0
        unsupported_claims_count = 0

        from narrative_copilot.schemas import ConflictClass

        per_class_stats: dict[str, dict[str, int]] = {
            c.value: {"tp": 0, "fp": 0, "fn": 0, "tn": 0} for c in ConflictClass
        }
        failure_cases: list[dict[str, Any]] = []
        extra_unmatched_alerts = 0

        for pack in packs:
            story_id = pack["story_id"]
            combined_md = "\n\n".join([c["text"] for c in pack["chapters"]])
            units, anchors, _ = self.importer.import_text(
                content=combined_md,
                format_type="markdown",
                project_id=story_id,
                revision_id="rev_eval",
                title=pack["title"],
            )

            # Map text snippets to anchors for gold resolution
            anchor_lookup = {a.anchor_id: a for a in anchors}

            def resolve_gold_anchor(
                evidence_text: str,
                cur_anchors: list[Any] = anchors,
                cur_units: list[Any] = units,
            ) -> str:
                clean_target = evidence_text.lower().strip()
                for a in cur_anchors:
                    if (
                        clean_target in a.normalized_quote.lower()
                        or a.normalized_quote.lower() in clean_target
                    ):
                        return str(a.anchor_id)
                for u in cur_units:
                    if u.unit_type.value == "block" and clean_target in u.text.lower():
                        for a in cur_anchors:
                            if a.block_id == u.unit_id:
                                return str(a.anchor_id)
                return ""

            # Extract memory & run continuity review
            memory = await self.memory_extractor.extract_memory(
                project_id=story_id,
                revision_id="rev_eval",
                units=units,
                anchors=anchors,
            )

            alerts = await self.continuity_engine.review_continuity(
                memory=memory,
                anchors=anchors,
                units=units,
            )

            anchor_id_set = set(anchor_lookup.keys())
            for al in alerts:
                total_alerts_generated += 1
                if (
                    al.evidence_a.anchor_id in anchor_id_set
                    and al.evidence_b.anchor_id in anchor_id_set
                ):
                    citation_valid_count += 1
                else:
                    unsupported_claims_count += 1

            # Available alerts pool for 1-to-1 matching
            available_alerts = list(alerts)

            # Match each benchmark case against gold evidence pairs
            for case in pack.get("benchmark_cases", []):
                expected = case["expected_is_contradiction"]
                case_class = case["conflict_class"]
                is_ambig = case.get("is_intentional_ambiguity", False)

                gold_aid_a = resolve_gold_anchor(case.get("evidence_a_text", ""))
                gold_aid_b = resolve_gold_anchor(case.get("evidence_b_text", ""))

                matched_alert = None
                matched_idx = -1

                for idx, al in enumerate(available_alerts):
                    # Match strictly by class and exact two-anchor gold evidence pair
                    class_matches = (
                        al.conflict_class.value == case_class or al.conflict_class == case_class
                    )
                    anchors_match = False
                    if gold_aid_a and gold_aid_b:
                        alert_anchors = {al.evidence_a.anchor_id, al.evidence_b.anchor_id}
                        gold_anchors = {gold_aid_a, gold_aid_b}
                        if alert_anchors == gold_anchors:
                            anchors_match = True
                    else:
                        anchors_match = True

                    if class_matches and anchors_match:
                        matched_alert = al
                        matched_idx = idx
                        break

                if is_ambig:
                    intentional_ambiguity_total += 1
                    if matched_alert is not None:
                        intentional_ambiguity_fps += 1

                if expected and matched_alert is not None:
                    true_positives += 1
                    per_class_stats[case_class]["tp"] += 1
                    available_alerts.pop(matched_idx)  # Consume matched alert
                elif not expected and matched_alert is None:
                    true_negatives += 1
                    per_class_stats[case_class]["tn"] += 1
                elif not expected and matched_alert is not None:
                    false_positives += 1
                    per_class_stats[case_class]["fp"] += 1
                    available_alerts.pop(matched_idx)
                    failure_cases.append(
                        {
                            "case_id": case["case_id"],
                            "type": "FALSE_POSITIVE",
                            "expected": expected,
                            "predicted": True,
                            "class": case_class,
                            "explanation": matched_alert.explanation,
                        }
                    )
                elif expected and matched_alert is None:
                    false_negatives += 1
                    per_class_stats[case_class]["fn"] += 1
                    failure_cases.append(
                        {
                            "case_id": case["case_id"],
                            "type": "FALSE_NEGATIVE",
                            "expected": expected,
                            "predicted": False,
                            "class": case_class,
                            "notes": case.get("notes", ""),
                        }
                    )

            # Any remaining unconsumed alerts in this pack are extra unmatched alerts
            pack_extra_alerts = len(available_alerts)
            extra_unmatched_alerts += pack_extra_alerts
            for leftover in available_alerts:
                cls_str = (
                    leftover.conflict_class.value
                    if hasattr(leftover.conflict_class, "value")
                    else str(leftover.conflict_class)
                )
                per_class_stats[cls_str]["fp"] += 1
                failure_cases.append(
                    {
                        "case_id": f"unmatched_{story_id}_{len(failure_cases)}",
                        "type": "EXTRA_UNMATCHED_ALERT",
                        "expected": False,
                        "predicted": True,
                        "class": cls_str,
                        "explanation": getattr(leftover, "explanation", "Unmatched spurious alert"),
                    }
                )

        total_fp_for_precision = false_positives + extra_unmatched_alerts
        precision = true_positives / max(true_positives + total_fp_for_precision, 1)
        recall = true_positives / max(true_positives + false_negatives, 1)
        f1 = (2 * precision * recall) / max(precision + recall, 1e-6)
        gold_case_fpr = false_positives / max(false_positives + true_negatives, 1)
        ambiguity_fpr = intentional_ambiguity_fps / max(intentional_ambiguity_total, 1)

        # Macro F1 & per-class breakdown
        class_f1s = []
        class_breakdown = {}
        for cname, counts in per_class_stats.items():
            if counts["tp"] + counts["fn"] == 0 and counts["tn"] > 0:
                specificity = counts["tn"] / max(counts["tn"] + counts["fp"], 1)
                class_breakdown[cname] = {
                    "precision": "NOT_APPLICABLE",
                    "recall": "NOT_APPLICABLE",
                    "f1": "NOT_APPLICABLE",
                    "specificity": round(specificity, 4),
                    "fpr": round(counts["fp"] / max(counts["fp"] + counts["tn"], 1), 4),
                    "tp": counts["tp"],
                    "fp": counts["fp"],
                    "tn": counts["tn"],
                    "fn": counts["fn"],
                    "support": counts["tp"] + counts["fn"] + counts["fp"] + counts["tn"],
                }
            else:
                c_p = counts["tp"] / max(counts["tp"] + counts["fp"], 1)
                c_r = counts["tp"] / max(counts["tp"] + counts["fn"], 1)
                c_f1 = (2 * c_p * c_r) / max(c_p + c_r, 1e-6)
                class_f1s.append(c_f1)
                class_breakdown[cname] = {
                    "precision": round(c_p, 4),
                    "recall": round(c_r, 4),
                    "f1": round(c_f1, 4),
                    "tp": counts["tp"],
                    "fp": counts["fp"],
                    "tn": counts["tn"],
                    "fn": counts["fn"],
                    "support": counts["tp"] + counts["fn"] + counts["fp"] + counts["tn"],
                }

        macro_f1 = sum(class_f1s) / max(len(class_f1s), 1)
        gold_cases_total = true_positives + true_negatives + false_positives + false_negatives
        positives_total = true_positives + false_negatives
        negatives_total = true_negatives + false_positives

        return {
            "total_cases": gold_cases_total,
            "held_out_gold_cases": gold_cases_total,
            "positive_gold_cases": positives_total,
            "negative_gold_cases": negatives_total,
            "true_positives": true_positives,
            "false_positives": false_positives,
            "true_negatives": true_negatives,
            "false_negatives": false_negatives,
            "extra_unmatched_alerts": extra_unmatched_alerts,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "macro_f1": round(macro_f1, 4),
            "gold_case_fpr": round(gold_case_fpr, 4),
            "false_positive_rate": round(gold_case_fpr, 4),
            "intentional_ambiguity_fpr": round(ambiguity_fpr, 4),
            "citation_validity_rate": round(
                citation_valid_count / max(total_alerts_generated, 1), 4
            ),
            "unsupported_claim_rate": round(
                unsupported_claims_count / max(total_alerts_generated, 1), 4
            ),
            "class_breakdown": class_breakdown,
            "failure_cases": failure_cases,
        }
