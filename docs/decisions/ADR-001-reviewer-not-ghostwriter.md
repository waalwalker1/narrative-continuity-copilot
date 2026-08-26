# ADR-001: Evidence-Grounded Reviewer Rather Than Autonomous Ghostwriter

## Status
Accepted

## Context
Generative AI tools often attempt to write prose autonomously or replace the author's voice. In long-form creative fiction, authorial agency and stylistic control are sacred. Ghostwriting models flatten nuances, invent unprompted canon, and disempower authors.

## Decision
The Narrative Continuity Copilot operates strictly as an evidence-grounded continuity reviewer and story-memory assistant. The system:
- Identifies potential contradictions and knowledge state leaks.
- Displays exact manuscript provenance for conflicting statements.
- Explains why passages may conflict.
- Lets the author decide whether an apparent conflict is intentional (e.g. mystery clue, rumor, dream, unreliable narrator).
- Never rewrites manuscript prose autonomously or mutates canon without explicit author confirmation.

## Consequences
- Preserves 100% author ownership and voice.
- Eliminates risk of unwanted plot alterations.
- Shifts engineering focus from text generation to high-precision retrieval, temporal reasoning, and provenance tracking.
