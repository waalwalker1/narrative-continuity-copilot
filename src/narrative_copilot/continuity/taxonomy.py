"""
12-Class Narrative Continuity Taxonomy definitions and descriptions.
"""

from narrative_copilot.schemas import ConflictClass

TAXONOMY_DESCRIPTIONS: dict[ConflictClass, str] = {
    ConflictClass.ATTRIBUTE_CONTRADICTION: "Physical or personal attribute (e.g. eye color, height, handedness) contradicts an earlier established fact.",
    ConflictClass.RELATIONSHIP_CONTRADICTION: "Kinship, marital, employment, or hierarchical relationship conflicts with prior statements.",
    ConflictClass.LOCATION_CONTINUITY: "Entity appears in an impossible or unprompted location without plausible travel timeline.",
    ConflictClass.OBJECT_STATE_CONTINUITY: "A destroyed, consumed, lost, or transferred object reappears in an incompatible state.",
    ConflictClass.INJURY_OR_PHYSICAL_STATE: "An injury (e.g. broken left arm vs right arm, blindness, scar) shifts or vanishes inconsistently.",
    ConflictClass.TIMELINE_ORDER_CONTRADICTION: "Chronological sequence of narrative events or cause-and-effect ordering is logically inverted.",
    ConflictClass.AGE_DATE_ARITHMETIC: "Character stated age, birth year, or calendar timeline arithmetic contradicts earlier dates.",
    ConflictClass.KNOWLEDGE_STATE_LEAK: "A character acts on, references, or discloses secret information before they learned it.",
    ConflictClass.WORLD_RULE_VIOLATION: "Established fictional world rule (magic system, technology limitation, law) is violated without exception.",
    ConflictClass.IDENTITY_ALIAS_CONFLICT: "Incompatible aliases or identity confusion across characters.",
    ConflictClass.POV_OR_EPISTEMIC_CONFLICT: "Contradiction arising from differing point-of-view beliefs, rumors, deception, or dreams.",
    ConflictClass.THREAD_STATUS_INCONSISTENCY: "A plot thread declared resolved is later treated as unaddressed, or vice versa.",
}
