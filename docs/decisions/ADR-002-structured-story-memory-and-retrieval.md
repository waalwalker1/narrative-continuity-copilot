# ADR-002: Structured Story Memory Combined with Hybrid Retrieval

## Status
Accepted

## Context
Raw RAG over unstructured chunks fails in long manuscripts because thematic similarities dilute exact factual assertions (e.g. eye color, timeline sequence, world rules). Pure knowledge graphs fail because fiction relies on nuanced context, epistemic uncertainty, and verbatim quote anchors.

## Decision
Combine structured narrative memory schemas (Entities, Facts, Relations, Timeline Events, World Rules, Story Threads) with Elasticsearch hybrid retrieval.
- Entities track aliases and canonical status.
- Facts model temporal validity, narrative scope (POV, dream, global canon), and epistemic status (rumor, observed, lie).
- Every memory item maintains explicit foreign keys to immutable `SourceAnchor` records.

## Consequences
- Enables deterministic candidate pairing and pre-filtering before LLM inference.
- Eliminates noise from semantically similar but factually irrelevant scenes.
