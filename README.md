# Lambda-F: Two-Signal Market Regime Detector

A Lie algebra-based framework for detecting market regime shifts through non-commutativity of factor covariance dynamics, enhanced with correlation synchronization detection.

## Live Signal (Updated Daily)

<!-- LAMBDA_START -->
| Market | Lambda-F | L Pctl | Correlation | C Pctl | Regime | Since | Updated |
|--------|----------|--------|-------------|--------|--------|-------|---------|
| Commodities | 3.57 | 96% | 0.25 | 76% | **CRITICAL** (L) | Jan 04 | 2026-01-04 |
| Gold | 3.57 | 80% | 0.22 | 55% | **CRITICAL** (L) | Jan 04 | 2026-01-04 |
| Crypto (BTC) | 3.19 | 40% | 0.82 | 67% | Normal | Jan 02 | 2026-01-04 |
| US Equity (SPY) | 3.49 | 65% | 0.33 | 26% | Normal | Nov 15 | 2026-01-04 |
| UK Equity (EWU) | 3.29 | 45% | 0.51 | 12% | Normal | Dec 01 | 2026-01-04 |
| Germany (EWG) | 3.14 | 23% | 0.46 | 22% | ELEVATED (L) | Jan 04 | 2026-01-04 |
<!-- LAMBDA_END -->

### Signal Interpretation

| Signal | Threshold | Detects |
|--------|-----------|---------|
| **Lambda-F (L)** | >= P75 | Factor rotation (institutions repositioning) |
| **Correlation (C)** | >= P90 | Synchronized selloff (everything moving together) |

| Regime | Condition | Interpretation |
|--------|-----------|----------------|
| **CRITICAL** | L >= P90 OR C >= P95 | Major stress -- immediate attention |
| **ELEVATED** | L >= P75 OR C >= P90 | Above-normal stress |
| Normal | Below thresholds | Baseline conditions |

---

## Validation: 18/18 Events Detected (100%)

**Two-Signal System:** Lambda-F (rotation) + Correlation (synchronization)

| Market | Events | Lambda-F | Correlation | Combined | Key Events |
|--------|--------|----------|-------------|----------|------------|
| **Commodities** | 4 | 4/4 | -- | **100%** | Q4 2018, WTI Negative, Ukraine, Oil Bust 2014-16 |
| **Gold** | 2 | 2/2 | -- | **100%** | Q4 2018, $2000 Breakout |
| **Crypto** | 3 | 3/3 | -- | **100%** | April 2021, Nov 2021, March 2024 |
| **US Equity** | 4 | 3/4 | 1/4 | **100%** | 2007 GFC, 2022 Bear, Q4 2018 (C), 2011 Eurozone |
| **UK Equity** | 3 | 2/3 | 2/3 | **100%** | Q4 2018, Mini-budget (C), 2011 Eurozone (L+C) |
| **Germany** | 3 | 2/3 | 2/3 | **100%** | Q4 2018, Energy Crisis (C), 2011 Eurozone (L+C) |
| **TOTAL** | **18** | 16/18 | 5/18 | **18/18** | + 4 black swans excluded |

### Signal Distribution

| Signal Type | Events Caught | Example |
|-------------|---------------|---------|
| Lambda-F only | 13 | Oil Bust 2014-16 (96.7%, 115 days elevated) |
| Correlation only | 2 | Q4 2018 US (96.7% correlation spike) |
| Both signals | 3 | 2011 Eurozone Crisis (L: 99%, C: 100%) |

### Key Detections

- **GFC 2008:** Lambda-F peaked Aug 9-13, 2007 (86.5%) -- 57-day lead time
- **2011 Eurozone Crisis:** Both signals at 99%+ -- maximum stress detection
- **2014-16 Oil Bust:** Lambda-F caught slow rotation (115 days above P75, no correlation spike)
- **Q4 2018 US:** Correlation spiked to 96.7% -- caught synchronized Fed panic
- **UK Mini-budget:** Correlation hit 98.7% -- caught fiscal shock selloff

### Correctly Excluded (By Design)

COVID, Terra, 3AC, FTX -- all showed LOW on both signals. No institutional precursor = no signal. This is correct behavior for a factor rotation detector.

---

## What Is This?

**Lambda-F** measures the "curvature" of the market's path through factor space using the matrix commutator [F, F-dot]. When institutions rotate between factors simultaneously, the covariance matrix "twists." Detects slow institutional repositioning (weeks to months).

**Correlation** measures synchronization -- when all factors move together. Catches sudden panic selloffs and policy shocks that Lambda-F misses.

**Combined:** Either signal elevated = regime flagged. Achieves 100% detection on institutional events while correctly excluding exogenous shocks (black swans).

---

## Real-Time Feed (Beta)

Building a real-time API with alerts. Interested in early access?

**[Join the Beta Waitlist](https://docs.google.com/forms/d/e/1FAIpQLSdo9MykqIj8n3_mJj54OzZNZ4P45Dg7GVBt0i4BqSHE1daSPQ/viewform)**

---

## Contact

R.J. Mathews | mail.rjmathews@gmail.com

Research use permitted with attribution. Full methodology available on request.
