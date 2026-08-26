# ADR-004: Stable Block UUIDs and Context Hashing for Provenance Anchors

## Status
Accepted

## Context
Standard character offsets (e.g. char 12400 to 12450) become completely invalid when an author inserts or deletes a single word earlier in the manuscript.

## Decision
Assign persistent UUIDs to each paragraph/block and embed custom block attributes into the Quill 2 editor representation.
Each `SourceAnchor` contains:
- `block_id`
- `char_start` and `char_end` relative to the block
- `text_hash` (SHA-256 of normalized quote)
- `previous_block_hash` and `next_block_hash`

Re-anchoring algorithm uses exact block matches, substring search, and SequenceMatcher fuzzy alignment, invalidating cleanly when confidence falls below threshold.

## Consequences
- Preserves citation integrity across edits.
- Eliminates citation drift.
