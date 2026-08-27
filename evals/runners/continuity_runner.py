"""
End-to-end Continuity Evaluation Runner.
Evaluates accuracy, per-class metrics, intentional ambiguity handling, citation validity, and failure cases.
"""

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from narrative_copilot.continuity.engine import ContinuityReasoningEngine
from narrative_copilot.ingestion.importer import ManuscriptImporter
from narrative_copilot.llm.deterministic_fixture import DeterministicFixtureLLMProvider
from narrative_copilot.memory.extractor import StoryMemoryExtractor


class ContinuityEvaluator:
    def __init__(self, fixtures_path: Path) -> None:
        self.fixtures_path = fixtures_path
        self.llm_provider = DeterministicFixtureLLMProvider()
        self.memory_extractor = StoryMemoryExtractor(self.llm_provider)
        self.continuity_engine = ContinuityReasoningEngine(self.llm_provider)
        self.importer = ManuscriptImporter()

    async def run_evaluation(self) -> dict[str, Any]:
        packs_file = self.fixtures_path / "story_packs.json"
        with open(packs_file, encoding="utf-8") as f:
            packs = json.load(f)

        true_positives = 0
        false_positives = 0
        true_negatives = 0
        false_negatives = 0

        intentional_ambiguity_total = 0
        intentional_ambiguity_fps = 0

        citation_valid_count = 0
        total_alerts_generated = 0
        unsupported_claims_count = 0

        per_class_stats: dict[str, dict[str, int]] = defaultdict(
            lambda: {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
        )
        failure_cases: list[dict[str, Any]] = []

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

            anchor_id_set = {a.anchor_id for a in anchors}
            for al in alerts:
                total_alerts_generated += 1
                if (
                    al.evidence_a.anchor_id in anchor_id_set
                    and al.evidence_b.anchor_id in anchor_id_set
                ):
                    citation_valid_count += 1
                else:
                    unsupported_claims_count += 1

            # Match against benchmark cases
            for case in pack.get("benchmark_cases", []):
                expected = case["expected_is_contradiction"]
                case_class = case["conflict_class"]
                is_ambig = case.get("is_intentional_ambiguity", False)

                # Did the system flag a contradiction for this case's predicate?
                # Matching by predicate and entity
                predicted = False
                matched_alert = None
                for al in alerts:
                    if (
                        al.conflict_class.value == case_class
                        or case["predicate"].lower() in al.explanation.lower()
                    ):
                        predicted = True
                        matched_alert = al
                        break

                if is_ambig:
                    intentional_ambiguity_total += 1
                    if predicted:
                        intentional_ambiguity_fps += 1

                if expected and predicted:
                    true_positives += 1
                    per_class_stats[case_class]["tp"] += 1
                elif not expected and not predicted:
                    true_negatives += 1
                    per_class_stats[case_class]["tn"] += 1
                elif not expected and predicted:
                    false_positives += 1
                    per_class_stats[case_class]["fp"] += 1
                    failure_cases.append(
                        {
                            "case_id": case["case_id"],
                            "type": "FALSE_POSITIVE",
                            "expected": expected,
                            "predicted": predicted,
                            "class": case_class,
                            "explanation": matched_alert.explanation if matched_alert else "",
                        }
                    )
                elif expected and not predicted:
                    false_negatives += 1
                    per_class_stats[case_class]["fn"] += 1
                    failure_cases.append(
                        {
                            "case_id": case["case_id"],
                            "type": "FALSE_NEGATIVE",
                            "expected": expected,
                            "predicted": predicted,
                            "class": case_class,
                            "notes": case.get("notes", ""),
                        }
                    )

        total = true_positives + false_positives + true_negatives + false_negatives
        precision = true_positives / max(true_positives + false_positives, 1)
        recall = true_positives / max(true_positives + false_negatives, 1)
        f1 = (2 * precision * recall) / max(precision + recall, 1e-6)
        fp_rate = false_positives / max(false_positives + true_negatives, 1)
        ambiguity_fpr = intentional_ambiguity_fps / max(intentional_ambiguity_total, 1)

        # Macro F1
        class_f1s = []
        class_breakdown = {}
        for cname, counts in per_class_stats.items():
            if counts["tp"] + counts["fn"] == 0 and counts["tn"] > 0:
                # Pure hard negative / intentional ambiguity class
                c_p = 1.0 if counts["fp"] == 0 else 0.0
                c_r = 1.0 if counts["fp"] == 0 else 0.0
                c_f1 = 1.0 if counts["fp"] == 0 else 0.0
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
        citation_validity = citation_valid_count / max(total_alerts_generated, 1)
        unsupported_rate = unsupported_claims_count / max(total_alerts_generated, 1)

        return {
            "total_cases": total,
            "true_positives": true_positives,
            "false_positives": false_positives,
            "true_negatives": true_negatives,
            "false_negatives": false_negatives,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "macro_f1": round(macro_f1, 4),
            "false_positive_rate": round(fp_rate, 4),
            "intentional_ambiguity_fpr": round(ambiguity_fpr, 4),
            "citation_validity_rate": round(citation_validity, 4),
            "unsupported_claim_rate": round(unsupported_rate, 4),
            "class_breakdown": class_breakdown,
            "failure_cases": failure_cases[:10],
        }
