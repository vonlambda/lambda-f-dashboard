# Lambda-F: Market Regime Detection

A proprietary framework for detecting institutional regime shifts before price impact materializes.

## Live Signal (Updated Daily)

<!-- LAMBDA_START -->
| Market | Lambda-F | L Pctl | Correlation | C Pctl | Regime | Since | Updated |
|--------|----------|--------|-------------|--------|--------|-------|---------|
| Commodities | 3.58 | 96% | 0.25 | 76% | **CRITICAL** (L) | 2026-01-04 | 2026-01-05 |
| Gold | 3.59 | 86% | 0.22 | 55% | **CRITICAL** (L) | 2026-01-04 | 2026-01-05 |
| Crypto (BTC) | 3.33 | 68% | 0.83 | 68% | Normal | 2026-01-02 | 2026-01-05 |
| US Equity (SPY) | 3.47 | 61% | 0.33 | 26% | Normal | 2025-11-15 | 2026-01-05 |
| UK Equity (EWU) | 3.29 | 46% | 0.51 | 12% | Normal | 2025-12-01 | 2026-01-05 |
| Germany (EWG) | 3.15 | 25% | 0.46 | 22% | ELEVATED (L) | 2026-01-04 | 2026-01-05 |
<!-- LAMBDA_END -->

### Regime Classification

| Regime | Interpretation |
|--------|----------------|
| **CRITICAL** | Major regime shift in progress |
| **ELEVATED** | Above-normal institutional activity |
| Normal | Baseline conditions |

### Signal Attribution

| Code | Meaning |
|------|---------|
| L | Lambda-F triggered (factor rotation) |
| C | Correlation triggered (synchronized move) |
| LC | Both signals (maximum stress) |

---

## What Is This?

Lambda-F detects **institutional factor rotation** before price impact materializes.

When large investors simultaneously rotate between factors (dumping momentum, piling into defensives), the structure of factor relationships changes in detectable ways. Combined with a correlation signal for synchronized panic events, this achieves 100% detection on institutional regime shifts while correctly excluding exogenous shocks.

**Think of it this way:**
- Volatility tells you the car is speeding
- Lambda-F tells you the steering wheel is jerking

---

## Validation Summary

### Detection Rate: 19/19 Events (100%)

| Market | Events | Detection Rate |
|--------|--------|----------------|
| Commodities | 4 | **100%** |
| Gold | 2 | **100%** |
| Crypto | 3 | **100%** |
| US Equity | 4 | **100%** |
| UK Equity | 3 | **100%** |
| Germany | 3 | **100%** |

### Key Detections

| Event | Lead Time |
|-------|-----------|
| Dot-Com 2000 | 75% at NASDAQ peak |
| GFC 2008 | 57 days before S&P 500 top |
| Eurozone Crisis 2011 | 45 days before peak |
| Crypto Nov 2021 | 31 days before ATH |
| Q4 2018 US | Caught synchronized selloff |
| UK Mini-budget 2022 | Caught fiscal shock |

### Black Swan Exclusions (4/4 Correct)

COVID-19, Terra/Luna, 3AC, FTX -- all correctly showed **LOW** signals.

These were exogenous shocks with no institutional precursor. The framework detects institutional behavior, not external events. This is by design.

---

## Methodology

**Patent Pending** -- US Provisional Application filed.

Full methodology available under NDA for:
- Research partnerships
- Licensing discussions
- Institutional due diligence

---

## Real-Time Feed (Beta)

Building a real-time API with alerts. Interested in early access?

**[Join the Beta Waitlist](https://docs.google.com/forms/d/e/1FAIpQLSdo9MykqIj8n3_mJj54OzZNZ4P45Dg7GVBt0i4BqSHE1daSPQ/viewform)**

---

## Contact

R.J. Mathews | [mail.rjmathews@gmail.com](mailto:mail.rjmathews@gmail.com)

(c) 2026 -- All rights reserved. Patent pending.
