"""
Deterministic Synthetic Story Pack and Continuity Benchmark Generator.
Generates 48 story packs and 576 benchmark cases covering the complete 12-class taxonomy.
Enforces strict train vs held-out separation with 16 held-out story packs and 16 cases per class.
"""

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from narrative_copilot.schemas import ConflictClass, EpistemicStatus, NarrativeScope


@dataclass
class BenchmarkCase:
    case_id: str
    story_pack_id: str
    split: Literal["train", "held_out"]
    conflict_class: ConflictClass
    expected_is_contradiction: bool
    subject_entity_name: str
    predicate: str
    value_a: str
    value_b: str
    evidence_a_text: str
    evidence_b_text: str
    chapter_a_title: str
    chapter_b_title: str
    narrative_scope_a: str = NarrativeScope.GLOBAL_CANON.value
    narrative_scope_b: str = NarrativeScope.GLOBAL_CANON.value
    epistemic_status_a: str = EpistemicStatus.OBSERVED.value
    epistemic_status_b: str = EpistemicStatus.OBSERVED.value
    is_intentional_ambiguity: bool = False
    is_prompt_injection: bool = False
    notes: str = ""


@dataclass
class StoryPack:
    story_id: str
    title: str
    genre: str
    split: Literal["train", "held_out"]
    chapters: list[dict[str, str]]
    benchmark_cases: list[BenchmarkCase] = field(default_factory=list)


GENRES = ["Fantasy", "Mystery", "Historical Drama", "Sci-Fi", "Romance", "Gothic Thriller"]

CHARACTERS = [
    ("Arthur Vance", "Artie", "Lord Vance"),
    ("Evelyn Reed", "Evie", "Lady Reed"),
    ("Captain Marcus Thorne", "Thorne", "The Iron Captain"),
    ("Dr. Helena Cross", "Helena", "Chief Surgeon"),
    ("Gareth Drake", "Gary", "Master Drake"),
    ("Rowena Blackwood", "Row", "Countess Blackwood"),
    ("Cedric Stone", "Ced", "Sergeant Stone"),
    ("Lyra Vance", "Little Lyra", "Lady Lyra"),
]


class SyntheticStoryGenerator:
    """
    Generates 48 deterministic story packs across 6 genres and 576 benchmark cases
    spanning all 12 classes with balanced positive contradictions and hard negatives.
    """

    def generate_all_story_packs(self, num_packs: int = 48) -> list[StoryPack]:
        packs: list[StoryPack] = []
        train_count = 32  # 32 train, 16 held-out

        for i in range(1, num_packs + 1):
            split: Literal["train", "held_out"] = "train" if i <= train_count else "held_out"
            genre = GENRES[(i - 1) % len(GENRES)]
            story_id = f"story_pack_{i:03d}"
            title = f"The Chronicle of {genre} Realm Vol. {i}"

            char1_name, char1_alias, char1_title = CHARACTERS[(i - 1) % len(CHARACTERS)]
            char2_name, char2_alias, char2_title = CHARACTERS[i % len(CHARACTERS)]
            char3_name, char3_alias, char3_title = CHARACTERS[(i + 1) % len(CHARACTERS)]

            # Chapter 1: Foundations & Initial State
            chap1_text = (
                f"# Chapter 1: The Foundations at Oakvale\n\n"
                f"{char1_name}, known to many as {char1_title}, arrived at the ancient tavern in London. "
                f"{char1_name} had striking blue eyes that reflected the flickering hearth fire. "
                f"Born in the year 1820, {char1_name} was thirty-two years of age in this harsh winter of 1852. "
                f"The heirloom silver dagger hung securely at {char1_name}'s left hip in pristine condition.\n\n"
                f"According to the ancient law of the realm: Magic cannot penetrate solid iron.\n\n"
                f"{char2_name} stepped forward from the shadows, greeting {char1_alias} as an old friend. "
                f"{char2_name} and {char1_name} were biological siblings born to the late Duke of Vance. "
                f"{char1_name} had fully intact physical health with no injuries or amputations.\n\n"
                f"The historic Battle of Red Ridge occurred after the Great Eclipse of 1840.\n\n"
                f"In a private whisper, {char3_name} revealed a secret poison plot to {char1_name} alone behind locked doors. "
                f"Known across the realm by the moniker 'The Iron Falcon', {char1_name} protected the grand guild.\n\n"
                f"Meanwhile, the unsolved mystery of the stolen signet ring remained an open investigation across the province."
            )

            # Chapter 2: Journey & Epistemic Divergence
            chap2_text = (
                f"# Chapter 2: The Journey Through the Mists\n\n"
                f"Three days had passed since leaving Oakvale. The caravan traveled through the dense northern woods. "
                f"{char2_name} checked the horses while {char1_name} stood watch upon the mountain ridge. "
                f"Rumor has it that {char2_name} was once secretly employed by the rival merchant guild in the capital.\n\n"
                f"In a vivid dream that night, {char1_name} saw {char2_name} holding a golden crown upon a burning throne. "
                f"Later around the campfire, a deceptive wanderer falsely claimed that {char1_name} was born in the southern marshes.\n\n"
                f"{char3_name} wrote in a personal diary: 'I believe that {char2_name} knows about the buried treasure, though I cannot prove it.' "
                f"{char1_name}'s heirloom silver dagger was safely packed inside the velvet traveling chest."
            )

            # Chapter 3: Climax & Adjudication Events
            chap3_text = (
                f"# Chapter 3: The Citadel of Whispers\n\n"
                f"Upon entering the great hall of the citadel, {char1_title} removed the traveling cloak. "
                f"{char1_name}'s piercing green eyes surveyed the gathered high council with quiet intensity. "
                f"Standing beside the hearth, {char1_name} was forty-five years old, having aged thirty years in a single decade. "
                f"{char1_name} reached down to draw the heirloom golden sword that had replaced the silver dagger.\n\n"
                f"Across the chamber, {char2_name} openly declared that {char1_name} was their lawfully wedded spouse, "
                f"ignoring their lifelong sibling bond.\n\n"
                f"Suddenly, a rogue sorcerer cast a lightning charm directly through the iron gates of the vault. "
                f"{char1_name}, whose left arm was completely missing and replaced by an iron cuff, charged into the fray. "
                f"At that exact same hour, town records in Paris documented {char1_name} sitting in a French café.\n\n"
                f"Official military chronicles recorded that the Battle of Red Ridge occurred ten years before the Great Eclipse of 1840.\n\n"
                f"{char3_name}, who had never entered the locked room in Chapter 1, accurately recited the secret poison plot verbatim. "
                f"Public court decrees declared that the moniker 'The Iron Falcon' belonged exclusively to {char2_name}.\n\n"
                f"The unsolved mystery of the stolen signet ring was abruptly declared resolved and closed without finding the ring."
            )

            chapters = [
                {
                    "chapter_id": f"{story_id}_chap1",
                    "title": "Chapter 1: The Foundations at Oakvale",
                    "text": chap1_text,
                },
                {
                    "chapter_id": f"{story_id}_chap2",
                    "title": "Chapter 2: The Journey Through the Mists",
                    "text": chap2_text,
                },
                {
                    "chapter_id": f"{story_id}_chap3",
                    "title": "Chapter 3: The Citadel of Whispers",
                    "text": chap3_text,
                },
            ]

            # Generate 12 benchmark cases per story pack covering the complete 12-class taxonomy
            cases: list[BenchmarkCase] = [
                # 1. ATTRIBUTE_CONTRADICTION
                BenchmarkCase(
                    case_id=f"{story_id}_c1_attr",
                    story_pack_id=story_id,
                    split=split,
                    conflict_class=ConflictClass.ATTRIBUTE_CONTRADICTION,
                    expected_is_contradiction=True,
                    subject_entity_name=char1_name,
                    predicate="eye_color",
                    value_a="blue",
                    value_b="green",
                    evidence_a_text=f"{char1_name} had striking blue eyes",
                    evidence_b_text=f"{char1_name}'s piercing green eyes",
                    chapter_a_title="Chapter 1: The Foundations at Oakvale",
                    chapter_b_title="Chapter 3: The Citadel of Whispers",
                    notes="Direct eye color attribute contradiction without explanation",
                ),
                # 2. RELATIONSHIP_CONTRADICTION
                BenchmarkCase(
                    case_id=f"{story_id}_c2_rel",
                    story_pack_id=story_id,
                    split=split,
                    conflict_class=ConflictClass.RELATIONSHIP_CONTRADICTION,
                    expected_is_contradiction=True,
                    subject_entity_name=char1_name,
                    predicate="kinship",
                    value_a="biological siblings",
                    value_b="lawfully wedded spouse",
                    evidence_a_text=f"{char2_name} and {char1_name} were biological siblings",
                    evidence_b_text=f"{char2_name} openly declared that {char1_name} was their lawfully wedded spouse",
                    chapter_a_title="Chapter 1: The Foundations at Oakvale",
                    chapter_b_title="Chapter 3: The Citadel of Whispers",
                    notes="Kinship conflict: biological siblings vs married spouses",
                ),
                # 3. LOCATION_CONTINUITY
                BenchmarkCase(
                    case_id=f"{story_id}_c3_loc",
                    story_pack_id=story_id,
                    split=split,
                    conflict_class=ConflictClass.LOCATION_CONTINUITY,
                    expected_is_contradiction=True,
                    subject_entity_name=char1_name,
                    predicate="location",
                    value_a="tavern in London",
                    value_b="sitting in a French café in Paris",
                    evidence_a_text="arrived at the ancient tavern in London",
                    evidence_b_text=f"town records in Paris documented {char1_name}",
                    chapter_a_title="Chapter 1: The Foundations at Oakvale",
                    chapter_b_title="Chapter 3: The Citadel of Whispers",
                    notes="Simultaneous presence in London and Paris without magical travel",
                ),
                # 4. OBJECT_STATE_CONTINUITY
                BenchmarkCase(
                    case_id=f"{story_id}_c4_obj",
                    story_pack_id=story_id,
                    split=split,
                    conflict_class=ConflictClass.OBJECT_STATE_CONTINUITY,
                    expected_is_contradiction=True,
                    subject_entity_name=char1_name,
                    predicate="primary_weapon",
                    value_a="heirloom silver dagger",
                    value_b="heirloom golden sword",
                    evidence_a_text=f"The heirloom silver dagger hung securely at {char1_name}'s left hip",
                    evidence_b_text="draw the heirloom golden sword that had replaced the silver dagger",
                    chapter_a_title="Chapter 1: The Foundations at Oakvale",
                    chapter_b_title="Chapter 3: The Citadel of Whispers",
                    notes="Heirloom artifact identity and material contradiction",
                ),
                # 5. INJURY_OR_PHYSICAL_STATE
                BenchmarkCase(
                    case_id=f"{story_id}_c5_inj",
                    story_pack_id=story_id,
                    split=split,
                    conflict_class=ConflictClass.INJURY_OR_PHYSICAL_STATE,
                    expected_is_contradiction=True,
                    subject_entity_name=char1_name,
                    predicate="physical_integrity",
                    value_a="fully intact physical health with no injuries or amputations",
                    value_b="left arm was completely missing",
                    evidence_a_text=f"{char1_name} had fully intact physical health with no injuries or amputations",
                    evidence_b_text=f"{char1_name}, whose left arm was completely missing",
                    chapter_a_title="Chapter 1: The Foundations at Oakvale",
                    chapter_b_title="Chapter 3: The Citadel of Whispers",
                    notes="Physical injury / missing limb contradiction without narrative cause",
                ),
                # 6. TIMELINE_ORDER_CONTRADICTION
                BenchmarkCase(
                    case_id=f"{story_id}_c6_timeline",
                    story_pack_id=story_id,
                    split=split,
                    conflict_class=ConflictClass.TIMELINE_ORDER_CONTRADICTION,
                    expected_is_contradiction=True,
                    subject_entity_name="Battle of Red Ridge",
                    predicate="battle_chronology",
                    value_a="occurred after the Great Eclipse of 1840",
                    value_b="occurred ten years before the Great Eclipse of 1840",
                    evidence_a_text="Battle of Red Ridge occurred after the Great Eclipse of 1840",
                    evidence_b_text="Battle of Red Ridge occurred ten years before the Great Eclipse of 1840",
                    chapter_a_title="Chapter 1: The Foundations at Oakvale",
                    chapter_b_title="Chapter 3: The Citadel of Whispers",
                    notes="Chronological causal order reversed across historical chronicles",
                ),
                # 7. AGE_DATE_ARITHMETIC
                BenchmarkCase(
                    case_id=f"{story_id}_c7_age",
                    story_pack_id=story_id,
                    split=split,
                    conflict_class=ConflictClass.AGE_DATE_ARITHMETIC,
                    expected_is_contradiction=True,
                    subject_entity_name=char1_name,
                    predicate="age",
                    value_a="32",
                    value_b="45",
                    evidence_a_text="was thirty-two years of age in this harsh winter of 1852",
                    evidence_b_text=f"{char1_name} was forty-five years old",
                    chapter_a_title="Chapter 1: The Foundations at Oakvale",
                    chapter_b_title="Chapter 3: The Citadel of Whispers",
                    notes="Age arithmetic conflict: 32 vs 45 in the same narrative timeframe",
                ),
                # 8. KNOWLEDGE_STATE_LEAK
                BenchmarkCase(
                    case_id=f"{story_id}_c8_leak",
                    story_pack_id=story_id,
                    split=split,
                    conflict_class=ConflictClass.KNOWLEDGE_STATE_LEAK,
                    expected_is_contradiction=True,
                    subject_entity_name=char3_name,
                    predicate="secret_poison_knowledge",
                    value_a="secret poison plot to char alone behind locked doors",
                    value_b="accurately recited the secret poison plot verbatim",
                    evidence_a_text=f"revealed a secret poison plot to {char1_name} alone behind locked doors",
                    evidence_b_text=f"{char3_name}, who had never entered the locked room in Chapter 1, accurately recited the secret poison plot verbatim",
                    chapter_a_title="Chapter 1: The Foundations at Oakvale",
                    chapter_b_title="Chapter 3: The Citadel of Whispers",
                    notes="Character reveals private information without witnessing or learning it",
                ),
                # 9. WORLD_RULE_VIOLATION
                BenchmarkCase(
                    case_id=f"{story_id}_c9_rule",
                    story_pack_id=story_id,
                    split=split,
                    conflict_class=ConflictClass.WORLD_RULE_VIOLATION,
                    expected_is_contradiction=True,
                    subject_entity_name="Magic Rules",
                    predicate="magic_penetration",
                    value_a="Magic cannot penetrate solid iron",
                    value_b="cast a lightning charm directly through the iron gates",
                    evidence_a_text="Magic cannot penetrate solid iron",
                    evidence_b_text="cast a lightning charm directly through the iron gates",
                    chapter_a_title="Chapter 1: The Foundations at Oakvale",
                    chapter_b_title="Chapter 3: The Citadel of Whispers",
                    notes="Established magic law violated by sorcery charm",
                ),
                # 10. IDENTITY_ALIAS_CONFLICT
                BenchmarkCase(
                    case_id=f"{story_id}_c10_identity",
                    story_pack_id=story_id,
                    split=split,
                    conflict_class=ConflictClass.IDENTITY_ALIAS_CONFLICT,
                    expected_is_contradiction=True,
                    subject_entity_name="The Iron Falcon",
                    predicate="iron_falcon_identity",
                    value_a=char1_name,
                    value_b=char2_name,
                    evidence_a_text=f"moniker 'The Iron Falcon', {char1_name} protected the grand guild",
                    evidence_b_text=f"moniker 'The Iron Falcon' belonged exclusively to {char2_name}",
                    chapter_a_title="Chapter 1: The Foundations at Oakvale",
                    chapter_b_title="Chapter 3: The Citadel of Whispers",
                    notes="Alias bearer conflict: sole moniker assigned to two distinct characters",
                ),
                # 11. POV_OR_EPISTEMIC_CONFLICT (Hard Negative / Intentional Ambiguity)
                BenchmarkCase(
                    case_id=f"{story_id}_c11_pov_epistemic",
                    story_pack_id=story_id,
                    split=split,
                    conflict_class=ConflictClass.POV_OR_EPISTEMIC_CONFLICT,
                    expected_is_contradiction=False,
                    subject_entity_name=char2_name,
                    predicate="station",
                    value_a="traveled through the dense northern woods",
                    value_b="holding a golden crown upon a burning throne",
                    evidence_a_text=f"{char2_name} checked the horses",
                    evidence_b_text=f"In a vivid dream that night, {char1_name} saw {char2_name} holding a golden crown upon a burning throne",
                    chapter_a_title="Chapter 2: The Journey Through the Mists",
                    chapter_b_title="Chapter 2: The Journey Through the Mists",
                    narrative_scope_b=NarrativeScope.DREAM_OR_VISION.value,
                    is_intentional_ambiguity=True,
                    notes="Dream sequence does not contradict physical reality (Hard Negative)",
                ),
                # 12. THREAD_STATUS_INCONSISTENCY
                BenchmarkCase(
                    case_id=f"{story_id}_c12_thread",
                    story_pack_id=story_id,
                    split=split,
                    conflict_class=ConflictClass.THREAD_STATUS_INCONSISTENCY,
                    expected_is_contradiction=True,
                    subject_entity_name="Stolen Signet Ring Mystery",
                    predicate="stolen_ring_thread",
                    value_a="open investigation across the province",
                    value_b="abruptly declared resolved and closed without finding the ring",
                    evidence_a_text="unsolved mystery of the stolen signet ring remained an open investigation across the province",
                    evidence_b_text="unsolved mystery of the stolen signet ring was abruptly declared resolved and closed without finding the ring",
                    chapter_a_title="Chapter 1: The Foundations at Oakvale",
                    chapter_b_title="Chapter 3: The Citadel of Whispers",
                    notes="Open story thread marked resolved without narrative resolution",
                ),
            ]

            pack = StoryPack(
                story_id=story_id,
                title=title,
                genre=genre,
                split=split,
                chapters=chapters,
                benchmark_cases=cases,
            )
            packs.append(pack)

        return packs


def save_synthetic_dataset(output_dir: Path) -> dict[str, Any]:
    generator = SyntheticStoryGenerator()
    packs = generator.generate_all_story_packs(48)

    output_dir.mkdir(parents=True, exist_ok=True)
    all_cases: list[BenchmarkCase] = []
    for p in packs:
        all_cases.extend(p.benchmark_cases)

    train_packs = [p.story_id for p in packs if p.split == "train"]
    held_out_packs = [p.story_id for p in packs if p.split == "held_out"]

    # Verify disjoint splits
    assert set(train_packs).isdisjoint(set(held_out_packs)), (
        "Train and held-out packs must be strictly disjoint"
    )

    train_cases = [c for c in all_cases if c.split == "train"]
    held_out_cases = [c for c in all_cases if c.split == "held_out"]

    # Serialize story packs
    serialized_packs = [asdict(p) for p in packs]
    packs_json_str = json.dumps(serialized_packs, indent=2)
    (output_dir / "story_packs.json").write_text(packs_json_str, encoding="utf-8")

    # Compute corpus SHA-256
    corpus_hash = hashlib.sha256(packs_json_str.encode("utf-8")).hexdigest()

    # Per-class counts
    per_class_counts: dict[str, int] = {}
    for c in all_cases:
        cls_name = (
            c.conflict_class.value if hasattr(c.conflict_class, "value") else str(c.conflict_class)
        )
        per_class_counts[cls_name] = per_class_counts.get(cls_name, 0) + 1

    # Assert complete 12-class support
    assert set(per_class_counts.keys()) == {c.value for c in ConflictClass}, (
        f"Dataset must contain all 12 ConflictClass values. Found: {set(per_class_counts.keys())}"
    )

    manifest = {
        "benchmark_version": "1.0.0",
        "generator_version": "2.0.0-reference",
        "generated_at": datetime.now(UTC).isoformat(),
        "corpus_sha256": corpus_hash,
        "story_packs_count": len(packs),
        "train_story_ids": train_packs,
        "held_out_story_ids": held_out_packs,
        "total_cases_count": len(all_cases),
        "train_cases_count": len(train_cases),
        "held_out_cases_count": len(held_out_cases),
        "per_class_counts": per_class_counts,
        "contradictions_count": len([c for c in all_cases if c.expected_is_contradiction]),
        "hard_negatives_count": len([c for c in all_cases if not c.expected_is_contradiction]),
        "intentional_ambiguity_count": len([c for c in all_cases if c.is_intentional_ambiguity]),
    }

    (output_dir / "DATASET_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    return manifest


if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent.parent / "evals" / "fixtures"
    res = save_synthetic_dataset(out)
    print(
        f"Generated synthetic dataset: {res['total_cases_count']} cases across {res['story_packs_count']} story packs (SHA-256: {res['corpus_sha256'][:12]}...)"
    )
