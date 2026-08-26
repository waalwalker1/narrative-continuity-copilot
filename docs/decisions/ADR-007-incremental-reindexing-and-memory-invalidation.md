# ADR-007: Incremental Reindexing and Selective Memory Invalidation

## Status
Accepted

## Context
Re-embedding and re-evaluating an entire 100k-word novel on every minor author edit causes prohibitive latency and compute costs.

## Decision
Implement revision diffing that detects changed blocks:
- Re-anchor existing facts using sequence matching.
- Invalidate only stale facts anchored to modified/deleted blocks.
- Re-extract memory and re-embed only modified chunks.
- Re-evaluate continuity only for the impacted entity/predicate neighborhood.

## Consequences
- Reduces processing time by over 80% on standard typing and paragraph revisions.
