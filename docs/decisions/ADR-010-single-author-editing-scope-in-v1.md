# ADR-010: Single-Author Editorial Scope for Version 1.0

## Status
Accepted

## Context
Full real-time multi-user collaborative editing (e.g. ShareDB / Operational Transformation / CRDTs) introduces significant distributed concurrency complexity that distracts from the core narrative continuity problem.

## Decision
Scope Version 1.0 to single-author revision workflows:
- Chapter-scoped Quill 2 editing.
- Revision snapshot creation and diffing.
- Multi-user real-time collaboration is documented as a future reference architecture.

## Consequences
- Clean, maintainable architecture focusing on high-precision narrative memory and retrieval.
