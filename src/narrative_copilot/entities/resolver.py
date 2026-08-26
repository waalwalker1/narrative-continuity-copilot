"""
Entity and alias resolution engine.
Handles character name variants, nicknames, titles, and author-controlled entity splits and merges.
"""

import difflib

from pydantic import BaseModel

from narrative_copilot.schemas import CanonicalStatus, Entity

NICKNAME_MAP: dict[str, set[str]] = {
    "elizabeth": {"lizzy", "eliza", "beth", "betty"},
    "william": {"will", "bill", "billy", "liam"},
    "robert": {"bob", "bobby", "rob"},
    "richard": {"dick", "rick", "rich"},
    "margaret": {"maggie", "meg", "peggy"},
    "katherine": {"kate", "katie", "kitty", "kat"},
    "alexander": {"alex", "sasha", "alec"},
    "edward": {"ed", "eddie", "ted", "teddy"},
}

HONORIFICS = {
    "mr",
    "mr.",
    "mrs",
    "mrs.",
    "miss",
    "ms",
    "ms.",
    "dr",
    "dr.",
    "lord",
    "lady",
    "sir",
    "captain",
    "cpt",
    "cpt.",
    "colonel",
    "col",
    "major",
    "duke",
    "duchess",
    "earl",
    "count",
    "countess",
    "king",
    "queen",
    "prince",
    "princess",
    "professor",
    "prof",
    "prof.",
}


class MergeCandidate(BaseModel):
    primary_entity_id: str
    secondary_entity_id: str
    primary_name: str
    secondary_name: str
    similarity_score: float
    reason: str
    requires_author_confirmation: bool


class EntityResolver:
    """
    Resolves entity aliases and scores candidate merges while preventing false merges.
    """

    def normalize_name(self, name: str) -> str:
        """Strip honorifics, punctuation, and extra whitespace."""
        tokens = name.lower().split()
        cleaned = [t.strip(".,;:\"'") for t in tokens if t.strip(".,;:'") not in HONORIFICS]
        return " ".join(cleaned)

    def calculate_name_similarity(self, name_a: str, name_b: str) -> float:
        """
        Calculate lexical, nickname, and containment similarity between two names.
        """
        norm_a = self.normalize_name(name_a)
        norm_b = self.normalize_name(name_b)

        if not norm_a or not norm_b:
            return 0.0

        # Exact match after honorific removal (e.g. "Mr. Darcy" vs "Darcy")
        if norm_a == norm_b:
            return 0.95

        # Substring / containment (e.g. "Elizabeth Bennet" vs "Elizabeth")
        tokens_a = set(norm_a.split())
        tokens_b = set(norm_b.split())

        if tokens_a == tokens_b:
            return 1.0

        if tokens_a.issubset(tokens_b) or tokens_b.issubset(tokens_a):
            # If both have single words that match (e.g. Bennet), but different honorifics (Miss Bennet vs Mrs Bennet), prevent false merge
            return 0.75

        # Check nickname map
        first_a = norm_a.split()[0] if norm_a else ""
        first_b = norm_b.split()[0] if norm_b else ""
        if first_a and first_b:
            nicknames_a = NICKNAME_MAP.get(first_a, set())
            nicknames_b = NICKNAME_MAP.get(first_b, set())
            if first_b in nicknames_a or first_a in nicknames_b:
                return 0.85

        # Sequence matcher ratio
        return round(difflib.SequenceMatcher(None, norm_a, norm_b).ratio(), 3)

    def find_merge_candidates(
        self, entities: list[Entity], threshold: float = 0.70
    ) -> list[MergeCandidate]:
        """
        Identify ambiguous entity pairs that might refer to the same person/entity.
        """
        candidates: list[MergeCandidate] = []
        n = len(entities)

        for i in range(n):
            for j in range(i + 1, n):
                e1 = entities[i]
                e2 = entities[j]

                # Cannot merge different entity types (e.g. location and character)
                if e1.entity_type != e2.entity_type:
                    continue

                sim = self.calculate_name_similarity(e1.canonical_name, e2.canonical_name)

                # Also test existing aliases
                for a in e1.aliases:
                    sim = max(sim, self.calculate_name_similarity(a, e2.canonical_name))
                for a in e2.aliases:
                    sim = max(sim, self.calculate_name_similarity(e1.canonical_name, a))

                if sim >= threshold:
                    # Require author confirmation unless identical
                    requires_conf = sim < 0.95
                    candidates.append(
                        MergeCandidate(
                            primary_entity_id=e1.entity_id,
                            secondary_entity_id=e2.entity_id,
                            primary_name=e1.canonical_name,
                            secondary_name=e2.canonical_name,
                            similarity_score=sim,
                            reason=f"Lexical and nickname similarity ({sim:.1%}) between '{e1.canonical_name}' and '{e2.canonical_name}'",
                            requires_author_confirmation=requires_conf,
                        )
                    )

        candidates.sort(key=lambda c: c.similarity_score, reverse=True)
        return candidates

    def merge_entities(
        self,
        primary_entity: Entity,
        secondary_entities: list[Entity],
    ) -> Entity:
        """
        Merge multiple secondary entities into primary entity, unifying aliases and evidence.
        """
        merged_aliases = set(primary_entity.aliases)
        merged_anchors = set(primary_entity.evidence_anchor_ids)

        for sec in secondary_entities:
            merged_aliases.add(sec.canonical_name)
            merged_aliases.update(sec.aliases)
            merged_anchors.update(sec.evidence_anchor_ids)

        # Remove canonical name from aliases
        if primary_entity.canonical_name in merged_aliases:
            merged_aliases.remove(primary_entity.canonical_name)

        return primary_entity.model_copy(
            update={
                "aliases": sorted(merged_aliases),
                "evidence_anchor_ids": sorted(merged_anchors),
                "canonical_status": CanonicalStatus.AUTHOR_CONFIRMED,
            }
        )
