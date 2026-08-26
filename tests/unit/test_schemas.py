"""
Unit tests for domain schemas and data invariants.
"""

from narrative_copilot.schemas import (
    AuthorActionType,
    AuthorDecision,
    CanonicalStatus,
    ConflictClass,
    ContinuityAlert,
    EvidenceSnippet,
    ManuscriptProject,
    PrivacyMode,
    SourceAnchor,
)


def test_manuscript_project_creation() -> None:
    project = ManuscriptProject(title="The Silver Knight", genre_hint="Fantasy")
    assert project.title == "The Silver Knight"
    assert project.privacy_mode == PrivacyMode.LOCAL_ONLY
    assert project.language == "en"
    assert project.project_id is not None


def test_source_anchor_validation() -> None:
    anchor = SourceAnchor(
        project_id="proj_1",
        revision_id="rev_1",
        chapter_id="chap_1",
        block_id="blk_1",
        char_start=0,
        char_end=25,
        text_hash="abc123hash",
        normalized_quote="Lord Arthur examined the map.",
    )
    assert anchor.char_end == 25
    assert len(anchor.normalized_quote) < 2000


def test_continuity_alert_structure() -> None:
    ev_a = EvidenceSnippet(
        anchor_id="anc_1",
        chapter_id="chap_1",
        block_id="blk_1",
        char_start=0,
        char_end=20,
        text_snippet="He had blue eyes.",
        revision_id="rev_1",
    )
    ev_b = EvidenceSnippet(
        anchor_id="anc_2",
        chapter_id="chap_2",
        block_id="blk_2",
        char_start=0,
        char_end=20,
        text_snippet="He had green eyes.",
        revision_id="rev_1",
    )

    alert = ContinuityAlert(
        project_id="proj_1",
        revision_id="rev_1",
        conflict_class=ConflictClass.ATTRIBUTE_CONTRADICTION,
        confidence=0.95,
        explanation="Eye color contradicted between chapter 1 and 2.",
        evidence_a=ev_a,
        evidence_b=ev_b,
    )

    assert alert.conflict_class == ConflictClass.ATTRIBUTE_CONTRADICTION
    assert alert.confidence == 0.95
    assert alert.canonical_status == CanonicalStatus.PROPOSED
    assert alert.suppressed is False


def test_author_decision_action_types() -> None:
    dec = AuthorDecision(
        project_id="proj_1",
        alert_id="alt_1",
        action_type=AuthorActionType.MARK_INTENTIONAL,
        author_notes="Deliberate illusion magic disguise.",
    )
    assert dec.action_type == AuthorActionType.MARK_INTENTIONAL
    assert dec.author_notes == "Deliberate illusion magic disguise."
