# Methodology Overview

Lambda-F uses the matrix commutator [F, Ḟ] to measure non-commutativity
of factor covariance dynamics. Combined with a correlation synchronization
signal, the two-signal system achieves **80.9% detection (38/47)** on the
current validated event ledger under canonical Method C (see README
validation section; the earlier 94.9%/100% figures were produced on the
smaller 39-event ledger and are superseded — same methodology, larger
event set).

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
| TP threshold (headline / outcome ledger) | >=20% drawdown in 90d | Recent-calls auto-tracking |
| Lift-analysis threshold (separate study) | >=15% drawdown in 90d | Conditional drawdown table |
| Outcome window | 90 days | Both |
| Episode merge gap | 30 days | Mechanical exclusion rule |
| Reflexivity threshold | >=60 | Game-theoretic framework |

**Two drawdown thresholds exist and are different analyses**: the outcome
ledger scores TRUE_POSITIVE at >=20% (bear-market convention); the lift
table conditions on >=15%. Any quoted precision/lift number must state
which threshold produced it.

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

Canonical number: **80.9% detection (38/47)** on the current extended event
ledger under Method C (see README for per-market breakdown and the
supersession note on the earlier 37/39 = 94.9% figure, which applied to the
pre-expansion ledger). `events.csv` holds the audit trail; black swans
(COVID, Terra/Luna, 3AC, FTX) remain design-excluded for the pre-event
window per the mechanical exclusion rule.

**Detection rate is a sensitivity metric** (did the signal fire inside a
known event window). It is not comparable to, and must not be quoted
beside, live forward precision (P(event | signal)). See
`honest_scorecard.py` / `signals/scorecard.json` for the episode-level,
censoring-aware precision numbers: outcome calls are merged into episodes
(30-day gap rule) before scoring, open forward windows are excluded from
the denominator, and the strict Q4 channel is scored separately from the
breadth-tuned all-CRITICAL channel.
