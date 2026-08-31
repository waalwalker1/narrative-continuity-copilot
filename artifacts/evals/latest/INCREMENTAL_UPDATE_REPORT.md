# Incremental Indexing & Scoped Update Report

## Execution & Scope
- **Total Edit Scenarios Evaluated**: 100
- **Total Paragraph Blocks Processed**: 1000
- **Reprocessed Blocks**: 100
- **Chunks Reprocessed Ratio**: 10.0%
- **Re-anchor Retention Rate**: 90.0%

## Memory Invalidation & Discovery Performance
- **Applicable Stale Fact Scenarios**: 10
- **Stale Fact Removals Expected**: 10
- **Stale Fact Removals Correctly Processed**: 10
- **Stale Fact Removal Recall**: 100.0%
- **Stale Fact Invalidation Precision**: 100.0%
- **Stale Fact Status**: `MEASURED`
- **Fresh Fact Discovery Scenarios**: 100
- **Fresh Facts Expected**: 100
- **Fresh Facts Discovered**: 10
- **Fresh Fact Extraction Recall**: 10.0%

## Benchmark Limitations
Structured fresh-fact extraction is conservative under the deterministic reference extractor (discovering ~10% on explicit attribute statements).
