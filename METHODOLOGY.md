# Methodology Overview

Lambda-F uses the matrix commutator [F, Ḟ] to measure non-commutativity
of factor covariance dynamics, combined with a correlation synchronization
signal.

> **⚠️ RETRACTION (2026-07-28).** This document previously claimed
> **80.9% detection (38/47)** on a "current validated event ledger," and
> earlier **94.9% (37/39)** and **100%** figures. **All three are
> withdrawn. They are not supported by any event ledger that exists.**
>
> An internal provenance audit walked *every commit* of this repository's
> `events.csv`: the row count grows 22 → 23 → 25 → 29 → 33 → … → **37 and
> never reaches 39 or 47.** No 47-event ledger and no 39-event ledger were
> ever committed here or found on any machine searched. The "38/47" figure
> existed only in prose; a related "78.7% detection / 26.85% FPR" figure
> existed only in a source comment, citing a results document that does not
> exist. The claims outran the data they cited.
>
> **No replacement detection rate is offered here.** Re-scoring the
> surviving 37-event ledger to produce a substitute headline would be
> manufacturing a number under pressure, which is the failure being
> corrected. Any future retrospective figure must be pre-registered and
> published with the ledger and scoring script it came from.
>
> **What is real and materialized in this repository:** `events.csv` (the
> 37-event audit trail) and `signals/scorecard.json` — the episode-level,
> censoring-aware **forward precision** record described under *Validation*
> below. Those numbers are generated from committed data by
> `honest_scorecard.py` and are the ones to rely on.

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

Combined detection rate: **withdrawn** — the "100% (37/39 testable)" figure
rested on a 39-event ledger that was never materialized (see the retraction
at the top of this document). No replacement figure is offered.

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

**There is currently no canonical retrospective detection number.** The
previous "80.9% (38/47)" claim — and the "37/39 = 94.9%" figure it said it
superseded — are withdrawn as unsupported; see the retraction at the top of
this document. The per-market breakdown that appeared in the README was
computed against the same non-existent 47-event ledger and has been withdrawn
with it.

`events.csv` holds the materialized audit trail (**37 events**). Black swans
(COVID, Terra/Luna, 3AC, FTX) remain design-excluded for the pre-event window
per the mechanical exclusion rule.

The scoring rule itself (**Method C** — flag if any of `λ_days_p75 ≥ 3`,
`λ_peak ≥ P90`, `corr_days_p90 ≥ 3`, `corr_peak ≥ P95` triggers in the event
window) is unchanged and is not what was withdrawn. What was withdrawn is the
claim about what that rule scored, on a ledger that did not exist.

**Detection rate is a sensitivity metric** (did the signal fire inside a
known event window). It is not comparable to, and must not be quoted
beside, live forward precision (P(event | signal)). See
`honest_scorecard.py` / `signals/scorecard.json` for the episode-level,
censoring-aware precision numbers: outcome calls are merged into episodes
(30-day gap rule) before scoring, open forward windows are excluded from
the denominator, and the strict Q4 channel is scored separately from the
breadth-tuned all-CRITICAL channel.
