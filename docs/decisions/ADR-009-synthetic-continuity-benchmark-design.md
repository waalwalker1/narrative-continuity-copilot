# ADR-009: Synthetic Continuity Benchmark Generation

## Status
Accepted

## Context
Copyrighted contemporary novels cannot be freely redistributed in open-source repositories, and public-domain classic novels lack rich multi-version edit histories and balanced ground-truth continuity contradiction labels.

## Decision
Build a deterministic synthetic fiction generator producing:
- >= 36 story packs across 6 genres (Fantasy, Mystery, Historical Drama, Sci-Fi, Romance, Gothic Thriller).
- >= 180 benchmark cases covering the 12-class continuity taxonomy.
- Story-level splits (train vs held-out) to prevent data leakage.
- Clear distribution of genuine contradictions, hard negatives, intentional ambiguities, and revision edge cases.

## Consequences
- 100% original, unencumbered benchmark assets that can be generated deterministically on any machine.
