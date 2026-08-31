# Anchor Stability & Re-anchoring Report

## Aggregate Performance
- **Total Edit Operations Evaluated**: 220
- **Expected-Outcome Accuracy**: 88.6%
- **False Re-anchor Rate**: 0.0% (0 false re-anchors)
- **Exact Match Retention**: 25 (11.4%)

## Per-Class Accuracy & Precision
- **Exact Match Accuracy**: 100.0%
- **Realignment Accuracy**: 79.7%
- **Transfer Accuracy**: 100.0%
- **Invalidation Accuracy**: 100.0%
- **Invalidation Precision**: 49.0%

## Expected vs Actual Confusion Matrix
| Expected \ Actual | EXACT_MATCH | REALIGNED | TRANSFERRED_BLOCK | INVALIDATED | Total Expected |
|---|---|---|---|---|---|
| **EXACT_MATCH** | 25 | 0 | 0 | 0 | 25 |
| **REALIGNED** | 0 | 98 | 0 | 25 | 123 |
| **TRANSFERRED_BLOCK** | 0 | 0 | 48 | 0 | 48 |
| **INVALIDATED** | 0 | 0 | 0 | 24 | 24 |
| **Total Actual** | 25 | 98 | 48 | 49 | 220 |
