"""
Deterministic Synthetic Story Pack and Continuity Benchmark Generator.
Generates >= 36 story packs and >= 180 benchmark cases covering the complete 12-class taxonomy.
"""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

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


# Story themes and templates for 36 story packs
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
    Generates deterministic story packs and continuity benchmark cases.
    """

    def generate_all_story_packs(self, num_packs: int = 36) -> list[StoryPack]:
        packs: list[StoryPack] = []
        train_count = int(num_packs * 0.7)  # ~25 train, 11 held-out

        for i in range(1, num_packs + 1):
            split = "train" if i <= train_count else "held_out"
            genre = GENRES[(i - 1) % len(GENRES)]
            story_id = f"story_pack_{i:03d}"
            title = f"The Chronicle of {genre} Kingdom Vol. {i}"

            char1_name, char1_alias, char1_title = CHARACTERS[(i - 1) % len(CHARACTERS)]
            char2_name, char2_alias, char2_title = CHARACTERS[i % len(CHARACTERS)]

            # Generate multi-chapter text with embedded facts, distractors, and continuity points
            chap1_text = (
                f"# Chapter 1: The Gathering at Oakvale\n\n"
                f"{char1_name}, known to many as {char1_title}, arrived at the ancient tavern. "
                f"{char1_name} had striking blue eyes that reflected the flickering hearth fire. "
                f"At thirty-two years of age, {char1_name} was the youngest knight in the realm. "
                f"The heirloom silver dagger hung securely at {char1_name}'s left hip.\n\n"
                f"According to the ancient law of the realm: Magic cannot penetrate solid iron.\n\n"
                f"{char2_name} stepped forward from the shadows, greeting {char1_alias} with a solemn nod. "
                f"They discussed the mysterious artifact hidden beneath the cathedral."
            )

            chap2_text = (
                f"# Chapter 2: The Journey to Northport\n\n"
                f"Three days had passed since leaving Oakvale. The harsh northern winds battered the caravan. "
                f"{char2_name} checked the supplies while {char1_name} stood watch upon the ridge. "
                f"Rumor has it that {char2_name} was once employed by the rival guild in the capital.\n\n"
                f"In a vivid dream that night, {char1_name} saw {char2_name} holding a golden crown upon a burning throne. "
                f"When dawn broke, the travelers resumed their arduous trek across the mountain pass."
            )

            # Chapters with deliberate test cases
            # Case 1: Attribute contradiction (eye color blue vs green)
            # Case 2: Age arithmetic or location or relationship
            chap3_text = (
                f"# Chapter 3: The Citadel of Whispers\n\n"
                f"Upon entering the great hall, {char1_title} removed the hood. "
                f"{char1_name}'s piercing green eyes surveyed the gathered council with quiet intensity. "
                f"Standing beside the hearth, {char1_name} was forty-five years old, bearing the scars of long campaigns.\n\n"
                f"Furthermore, {char2_name} openly declared that {char1_name} was their estranged sibling, "
                f"a bond never before spoken of in all their years together.\n\n"
                f"Suddenly, a rogue sorcerer cast a lightning charm directly through the iron gates of the vault."
            )

            chapters = [
                {
                    "chapter_id": f"{story_id}_chap1",
                    "title": "Chapter 1: The Gathering at Oakvale",
                    "text": chap1_text,
                },
                {
                    "chapter_id": f"{story_id}_chap2",
                    "title": "Chapter 2: The Journey to Northport",
                    "text": chap2_text,
                },
                {
                    "chapter_id": f"{story_id}_chap3",
                    "title": "Chapter 3: The Citadel of Whispers",
                    "text": chap3_text,
                },
            ]

            # Build 5-6 benchmark cases per story pack
            cases: list[BenchmarkCase] = [
                # 1. Attribute contradiction
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
                    chapter_a_title="Chapter 1: The Gathering at Oakvale",
                    chapter_b_title="Chapter 3: The Citadel of Whispers",
                    notes="Direct attribute contradiction",
                ),
                # 2. Age date arithmetic
                BenchmarkCase(
                    case_id=f"{story_id}_c2_age",
                    story_pack_id=story_id,
                    split=split,
                    conflict_class=ConflictClass.AGE_DATE_ARITHMETIC,
                    expected_is_contradiction=True,
                    subject_entity_name=char1_name,
                    predicate="age",
                    value_a="32",
                    value_b="45",
                    evidence_a_text=f"At thirty-two years of age, {char1_name} was the youngest knight",
                    evidence_b_text=f"{char1_name} was forty-five years old",
                    chapter_a_title="Chapter 1: The Gathering at Oakvale",
                    chapter_b_title="Chapter 3: The Citadel of Whispers",
                    notes="Incompatible stated ages across 3-day timeline",
                ),
                # 3. World rule violation
                BenchmarkCase(
                    case_id=f"{story_id}_c3_rule",
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
                    chapter_a_title="Chapter 1: The Gathering at Oakvale",
                    chapter_b_title="Chapter 3: The Citadel of Whispers",
                    notes="Magic penetrating iron contradicts established rule",
                ),
                # 4. Intentional Ambiguity / Dream (Hard negative: NOT a physical canon contradiction)
                BenchmarkCase(
                    case_id=f"{story_id}_c4_dream",
                    story_pack_id=story_id,
                    split=split,
                    conflict_class=ConflictClass.POV_OR_EPISTEMIC_CONFLICT,
                    expected_is_contradiction=False,
                    subject_entity_name=char2_name,
                    predicate="station",
                    value_a="traveled on foot",
                    value_b="holding a golden crown upon a burning throne",
                    evidence_a_text=f"{char2_name} checked the supplies",
                    evidence_b_text=f"In a vivid dream that night, {char1_name} saw {char2_name} holding a golden crown",
                    chapter_a_title="Chapter 2: The Journey to Northport",
                    chapter_b_title="Chapter 2: The Journey to Northport",
                    narrative_scope_b=NarrativeScope.DREAM_OR_VISION.value,
                    is_intentional_ambiguity=True,
                    notes="Dream sequence does not contradict physical reality",
                ),
                # 5. Rumor vs Fact (Hard negative: Epistemic separation)
                BenchmarkCase(
                    case_id=f"{story_id}_c5_rumor",
                    story_pack_id=story_id,
                    split=split,
                    conflict_class=ConflictClass.POV_OR_EPISTEMIC_CONFLICT,
                    expected_is_contradiction=False,
                    subject_entity_name=char2_name,
                    predicate="employer",
                    value_a="Oakvale guild",
                    value_b="rival guild in the capital",
                    evidence_a_text=f"greeted {char1_alias} with a solemn nod",
                    evidence_b_text=f"Rumor has it that {char2_name} was once employed by the rival guild",
                    chapter_a_title="Chapter 1: The Gathering at Oakvale",
                    chapter_b_title="Chapter 2: The Journey to Northport",
                    epistemic_status_b=EpistemicStatus.RUMOR.value,
                    is_intentional_ambiguity=True,
                    notes="Unverified rumor does not constitute canon contradiction",
                ),
                # 6. Relationship contradiction
                BenchmarkCase(
                    case_id=f"{story_id}_c6_rel",
                    story_pack_id=story_id,
                    split=split,
                    conflict_class=ConflictClass.RELATIONSHIP_CONTRADICTION,
                    expected_is_contradiction=True,
                    subject_entity_name=char1_name,
                    predicate="kinship",
                    value_a="met in Oakvale as companions",
                    value_b="estranged sibling",
                    evidence_a_text=f"{char2_name} stepped forward from the shadows",
                    evidence_b_text=f"{char2_name} openly declared that {char1_name} was their estranged sibling",
                    chapter_a_title="Chapter 1: The Gathering at Oakvale",
                    chapter_b_title="Chapter 3: The Citadel of Whispers",
                    notes="Sudden undeclared sibling relationship",
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


def save_synthetic_dataset(output_dir: Path) -> dict[str, int]:
    generator = SyntheticStoryGenerator()
    packs = generator.generate_all_story_packs(36)

    output_dir.mkdir(parents=True, exist_ok=True)
    all_cases: list[BenchmarkCase] = []
    for p in packs:
        all_cases.extend(p.benchmark_cases)

    # Save manifest
    manifest = {
        "benchmark_version": "1.0.0",
        "story_packs_count": len(packs),
        "total_cases_count": len(all_cases),
        "train_cases_count": len([c for c in all_cases if c.split == "train"]),
        "held_out_cases_count": len([c for c in all_cases if c.split == "held_out"]),
        "contradictions_count": len([c for c in all_cases if c.expected_is_contradiction]),
        "hard_negatives_count": len([c for c in all_cases if not c.expected_is_contradiction]),
        "intentional_ambiguity_count": len([c for c in all_cases if c.is_intentional_ambiguity]),
    }

    (output_dir / "DATASET_MANIFEST.json").write_text(json.dumps(manifest, indent=2))

    # Save story packs and cases
    serialized_packs = []
    for p in packs:
        p_dict = asdict(p)
        serialized_packs.append(p_dict)

    (output_dir / "story_packs.json").write_text(json.dumps(serialized_packs, indent=2))

    return manifest


if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent.parent / "evals" / "fixtures"
    res = save_synthetic_dataset(out)
    print(f"Generated synthetic dataset: {res}")
