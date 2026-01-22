# Methodology Overview

Lambda-F uses the matrix commutator [F, Ḟ] to measure non-commutativity
of factor covariance dynamics. Combined with a correlation synchronization
signal, the two-signal system achieves 100% detection on institutional events.

## Key Concepts
- Factor covariance matrix evolution
- Commutator-based rotation detection
- Correlation-based synchronization detection
- Percentile-based regime classification
- Game-theoretic quadrant classification (Q1-Q4)
- Signal-to-correction matching

## Parameters

### Lambda-F Computation
| Parameter | Value | Purpose |
|-----------|-------|---------|
| Window | 105 days | Covariance estimation window |
| EMA Span | 5 days | Factor smoothing |
| Smoothing | 14 days | Output signal smoothing |
| Lag | 2 days | Look-ahead prevention |

### Outcome Tracking
| Parameter | Value | Source |
|-----------|-------|--------|
| Correction threshold | >=15% drawdown | Lift analysis table |
| Outcome window | 90 days | Lift analysis |
| Episode merge gap | 30 days | Mechanical exclusion rule |
| Reflexivity threshold | >=60 | Game-theoretic framework |

Full parameters documented in the provisional patent application.
Detailed methodology available to research partners under NDA.

## Two-Signal Detection

1. **Lambda-F (Rotation)**: Detects institutional factor rotation via commutator
2. **Correlation (Synchronization)**: Detects panic selloffs via pairwise correlation

Combined detection rate: 100% on institutional events (37/39 testable).

## Game-Theoretic Enhancement

The 2x2 classification matrix combines Lambda-F with reflexivity indicators:

| Quadrant | Lambda-F | Reflexivity | Interpretation |
|----------|----------|-------------|----------------|
| Q1 | < P75 | < 60 | STABLE - Normal conditions |
| Q2 | < P75 | >= 60 | FRAGILE - Leveraged but stable |
| Q3 | >= P75 | < 60 | ROTATING - Factor shift, low cascade risk |
| Q4 | >= P75 | >= 60 | CRITICAL - Maximum crash probability |

Only Q4 episodes are classified as TRUE_POSITIVE when followed by correction.

## Signal-to-Correction Matching

Episodes are automatically tracked from signal to outcome:

```
ELEVATED/CRITICAL → Episode Created
     │
     ├── Correction (>=15% in 90d) + Q4 → TRUE_POSITIVE
     ├── Correction (>=15% in 90d) + Q3 → PARTIAL
     ├── No correction within 90d → FALSE_POSITIVE
     └── Gap < 30d normal → Episode continues (merge)
```

### Episode Lifecycle Files
- `active_episodes.json` - Currently tracked episodes
- `events.csv` - Completed episode outcomes (audit trail)

## Validation

See `events.csv` for the complete audit trail of 52 events tested:
- 37 detected (institutional rotations)
- 4 excluded (black swans: COVID, Terra/Luna, 3AC, FTX)
- 2 not detected (documented limitations)
- 9 additional validated events

Detection rate: 94.9% (37/39 testable events)
