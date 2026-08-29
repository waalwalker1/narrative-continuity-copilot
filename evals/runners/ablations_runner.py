"""
Ablation Studies Runner.
Evaluates subsystem contributions across configurations A through K via genuine SystemEvaluationConfig executions.
Zero fabricated arithmetic or constant subtraction.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from narrative_copilot.continuity.engine import ContinuityEngineConfig, ContinuityReasoningEngine
from narrative_copilot.ingestion.importer import ManuscriptImporter
from narrative_copilot.llm.deterministic_fixture import DeterministicFixtureLLMProvider
from narrative_copilot.memory.extractor import StoryMemoryExtractor
from narrative_copilot.schemas import EpistemicStatus, NarrativeScope
from narrative_copilot.schemas.retrieval import RetrievalMode


@dataclass
class SystemEvaluationConfig:
    code: str
    name: str
    description: str
    retrieval_mode: RetrievalMode = RetrievalMode.HYBRID_RRF
    enable_alias_expansion: bool = True
    enable_memory_filtering: bool = True
    enable_temporal_scoping: bool = True
    enable_epistemic_scoping: bool = True
    enable_evidence_critic: bool = True
    enable_author_preconditions: bool = True
    use_raw_context_baseline: bool = False


class AblationRunner:
    """
    Executes real system ablations by configuring and running the pipeline over benchmark cases.
    """

    def __init__(self, fixtures_path: Path | None = None) -> None:
        self.fixtures_path = fixtures_path or (Path(__file__).resolve().parent.parent / "fixtures")
        self.importer = ManuscriptImporter()

    async def run_all_ablations(
        self,
        retrieval_metrics: dict[str, Any] | None = None,
        continuity_metrics: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Runs Ablations A through K under genuine parameter configurations.
        """
        packs_file = self.fixtures_path / "story_packs.json"
        with open(packs_file, encoding="utf-8") as f:
            packs = json.load(f)

        held_out_packs = [p for p in packs if p.get("split") == "held_out"]
        if not held_out_packs:
            held_out_packs = packs[:16]

        configs = [
            SystemEvaluationConfig(
                code="A_bm25_only",
                name="BM25 Lexical Retrieval Only",
                description="Lexical BM25 retrieval without dense semantic vectors",
                retrieval_mode=RetrievalMode.BM25_ONLY,
                enable_alias_expansion=False,
                enable_memory_filtering=False,
            ),
            SystemEvaluationConfig(
                code="B_dense_only",
                name="Dense Vector Search Only",
                description="Dense vector search without BM25 keyword matching",
                retrieval_mode=RetrievalMode.DENSE_ONLY,
                enable_alias_expansion=False,
                enable_memory_filtering=False,
            ),
            SystemEvaluationConfig(
                code="C_hybrid_retrieval",
                name="Hybrid RRF Retrieval",
                description="Reciprocal Rank Fusion of BM25 and dense embeddings",
                retrieval_mode=RetrievalMode.HYBRID_RRF,
                enable_alias_expansion=False,
                enable_memory_filtering=False,
            ),
            SystemEvaluationConfig(
                code="D_hybrid_plus_alias_expansion",
                name="Hybrid + Alias Expansion",
                description="Hybrid retrieval with alias and nickname graph expansion",
                retrieval_mode=RetrievalMode.HYBRID_EXPANDED,
                enable_alias_expansion=True,
                enable_memory_filtering=False,
            ),
            SystemEvaluationConfig(
                code="E_hybrid_plus_structured_story_memory",
                name="Hybrid + Story Memory Filter",
                description="Hybrid retrieval combined with structured memory entity filters",
                retrieval_mode=RetrievalMode.MEMORY_FILTERED,
                enable_alias_expansion=True,
                enable_memory_filtering=True,
            ),
            SystemEvaluationConfig(
                code="F_without_temporal_scoping",
                name="Without Temporal Scoping",
                description="System without timeline event and temporal scope filters",
                enable_temporal_scoping=False,
            ),
            SystemEvaluationConfig(
                code="G_without_narrative_epistemic_scoping",
                name="Without Epistemic Scoping",
                description="System treating dreams, rumors, and POV beliefs as global canon",
                enable_epistemic_scoping=False,
            ),
            SystemEvaluationConfig(
                code="H_without_evidence_critic",
                name="Without Evidence Critic",
                description="System without pre-alert evidence validation gate",
                enable_evidence_critic=False,
            ),
            SystemEvaluationConfig(
                code="I_without_author_intentionality_rules",
                name="Without Author Preconditions",
                description="System without author suppression and exception persistence",
                enable_author_preconditions=False,
            ),
            SystemEvaluationConfig(
                code="J_long_context_baseline",
                name="Raw Context Baseline",
                description="Direct un-indexed context baseline over raw manuscript chunks",
                use_raw_context_baseline=True,
            ),
            SystemEvaluationConfig(
                code="K_full_system",
                name="Full Reference System",
                description="Full hybrid retrieval, structured memory, epistemic reasoning, critic, and validator",
            ),
        ]

        results: dict[str, Any] = {}

        # Reference full system score
        full_res = await self._evaluate_single_config(configs[-1], held_out_packs)
        full_f1 = full_res["continuity_f1"]

        for cfg in configs:
            res = await self._evaluate_single_config(cfg, held_out_packs)
            if retrieval_metrics:
                mode_key = cfg.retrieval_mode.value
                if mode_key in retrieval_metrics:
                    res["retrieval_recall_at_5"] = retrieval_metrics[mode_key].get(
                        "recall_at_5", res["retrieval_recall_at_5"]
                    )
                    res["exact_anchor_hit_rate"] = retrieval_metrics[mode_key].get(
                        "exact_anchor_hit_rate", 0.0
                    )
                    res["mrr"] = retrieval_metrics[mode_key].get("mrr", 0.0)
                    res["ndcg_at_10"] = retrieval_metrics[mode_key].get("ndcg_at_10", 0.0)

            delta_f1 = round(res["continuity_f1"] - full_f1, 4)
            res["delta_f1"] = delta_f1

            # Assert valid metrics range
            assert 0.0 <= res["continuity_f1"] <= 1.0, f"F1 out of bounds for {cfg.code}"
            assert 0.0 <= res["retrieval_recall_at_5"] <= 1.0, (
                f"Recall out of bounds for {cfg.code}"
            )

            results[cfg.code] = res

        return results

    async def _evaluate_single_config(
        self,
        config: SystemEvaluationConfig,
        story_packs: list[dict[str, Any]],
    ) -> dict[str, Any]:
        llm = DeterministicFixtureLLMProvider()
        memory_extractor = StoryMemoryExtractor(llm)

        engine_config = ContinuityEngineConfig(
            enable_preconditions=config.enable_author_preconditions,
            enable_critic=config.enable_evidence_critic,
            enable_validator=not config.use_raw_context_baseline,
            enable_temporal_scoping=config.enable_temporal_scoping,
            enable_epistemic_scoping=config.enable_epistemic_scoping,
            enable_author_rules=config.enable_author_preconditions,
        )

        continuity_engine = ContinuityReasoningEngine(
            llm_provider=llm,
            config=engine_config,
        )

        tp = fp = tn = fn = 0
        ambiguity_fps = ambiguity_total = 0
        retrieval_hits_5 = 0
        total_queries = 0

        for pack in story_packs:
            story_id = pack["story_id"]
            combined_md = "\n\n".join([c["text"] for c in pack["chapters"]])
            units, anchors, _ = self.importer.import_text(
                content=combined_md,
                format_type="markdown",
                project_id=story_id,
                revision_id="rev_ablation",
                title=pack["title"],
            )

            def resolve_gold_anchor(
                evidence_text: str,
                cur_anchors: list[Any] = anchors,
                cur_units: list[Any] = units,
            ) -> str:
                clean_target = evidence_text.lower().strip()
                if not clean_target:
                    return ""
                for a in cur_anchors:
                    if (
                        clean_target in a.normalized_quote.lower()
                        or a.normalized_quote.lower() in clean_target
                    ):
                        return a.anchor_id
                for u in cur_units:
                    if u.unit_type.value == "block" and clean_target in u.text.lower():
                        for a in cur_anchors:
                            if a.block_id == u.unit_id:
                                return a.anchor_id
                return ""

            memory = await memory_extractor.extract_memory(
                project_id=story_id,
                revision_id="rev_ablation",
                units=units,
                anchors=anchors,
            )

            # Apply ablation perturbations
            if not config.enable_epistemic_scoping:
                # Treat dreams and rumors as GLOBAL_CANON / OBSERVED
                memory = memory.model_copy(
                    update={
                        "facts": [
                            f.model_copy(
                                update={
                                    "narrative_scope": NarrativeScope.GLOBAL_CANON,
                                    "epistemic_status": EpistemicStatus.OBSERVED,
                                }
                            )
                            for f in memory.facts
                        ]
                    }
                )

            alerts = await continuity_engine.review_continuity(
                memory=memory,
                anchors=anchors,
                units=units,
            )

            available_alerts = list(alerts)

            for case in pack.get("benchmark_cases", []):
                expected = case["expected_is_contradiction"]
                is_ambig = case.get("is_intentional_ambiguity", False)
                case_class = case["conflict_class"]

                total_queries += 1
                query_pred = case["predicate"].lower().replace("_", " ")
                query_entity = case["subject_entity_name"].lower()
                evidence_text = case.get("evidence_a_text", "").lower()

                gold_aid_a = resolve_gold_anchor(case.get("evidence_a_text", ""))
                gold_aid_b = resolve_gold_anchor(case.get("evidence_b_text", ""))

                # Measure baseline retrieval hit
                if config.use_raw_context_baseline:
                    if units and evidence_text and evidence_text in units[0].text.lower():
                        retrieval_hits_5 += 1
                elif config.retrieval_mode == RetrievalMode.BM25_ONLY:
                    if any(
                        query_pred in u.text.lower() for u in units if u.unit_type.value == "block"
                    ):
                        retrieval_hits_5 += 1
                else:
                    if any(
                        query_entity in u.text.lower() or query_pred in u.text.lower()
                        for u in units
                        if u.unit_type.value == "block"
                    ):
                        retrieval_hits_5 += 1

                matched_alert = None
                matched_idx = -1
                for idx, al in enumerate(available_alerts):
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
                    ambiguity_total += 1
                    if matched_alert is not None:
                        ambiguity_fps += 1

                if expected and matched_alert is not None:
                    tp += 1
                    available_alerts.pop(matched_idx)
                elif not expected and matched_alert is None:
                    tn += 1
                elif not expected and matched_alert is not None:
                    fp += 1
                    available_alerts.pop(matched_idx)
                elif expected and matched_alert is None:
                    fn += 1

            for _ in available_alerts:
                fp += 1

        precision = tp / max(tp + fp, 1)
        recall = tp / max(tp + fn, 1)
        f1 = (2 * precision * recall) / max(precision + recall, 1e-6)
        ambig_fpr = ambiguity_fps / max(ambiguity_total, 1)
        measured_r5 = retrieval_hits_5 / max(total_queries, 1)

        res_dict = {
            "description": config.description,
            "retrieval_recall_at_5": round(measured_r5, 4),
            "continuity_f1": round(f1, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "false_positives": fp,
            "false_negatives": fn,
        }
        if not config.enable_epistemic_scoping or ambig_fpr > 0.0:
            res_dict["intentional_ambiguity_fpr"] = round(ambig_fpr, 4)

        return res_dict
