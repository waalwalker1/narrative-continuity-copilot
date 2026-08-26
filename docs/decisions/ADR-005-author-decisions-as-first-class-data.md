# ADR-005: Author Decisions as First-Class Relational Data

## Status
Accepted

## Context
When an author marks an apparent contradiction as intentional (e.g. character lie, mystery clue, unreliable narrator), future review passes must respect that decision rather than continuously raising duplicate alerts.

## Decision
Persist author decisions as first-class entities in SQLite:
- Actions: `MARK_INTENTIONAL`, `MARK_POV_BELIEF`, `MARK_RUMOR`, `MARK_UNRELIABLE`, `CREATE_WORLD_RULE_EXCEPTION`, `RESOLVE_WITH_CURRENT_FACT`, `SUPERSEDE_EARLIER_FACT`, `MERGE_ALIASES`, `SPLIT_ENTITY`, `IGNORE_ALERT`.
- Decisions update fact and alert canonical statuses and populate suppression keys for deterministic precondition filtering.

## Consequences
- The system learns the manuscript canon dynamically without altering creative prose.
