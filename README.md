# Lambda-F: Factor Rotation Stress Monitor

A Lie algebra-based framework for detecting market regime shifts through non-commutativity of factor covariance dynamics.

## Live Signal (Updated Daily)

<!-- LAMBDA_START -->
| Market | Lambda-F | Corr | Regime | Since | Updated |
|--------|----------|------|--------|-------|---------|
| Commodities | 96% | 76% | **CRITICAL** (L) | Jan 04 | 2026-01-04 |
| Gold | 80% | 55% | **CRITICAL** (L) | Jan 04 | 2026-01-04 |
| Crypto (BTC) | 40% | 67% | Normal | Jan 02 | 2026-01-04 |
| US Equity (SPY) | 65% | 26% | Normal | Nov 15 | 2026-01-04 |
| UK Equity (EWU) | 45% | 12% | Normal | Dec 01 | 2026-01-04 |
| Germany (EWG) | 23% | 22% | ELEVATED (L) | Jan 04 | 2026-01-04 |
<!-- LAMBDA_END -->

### Regime Classification

| Regime | Percentile | Interpretation |
|--------|------------|----------------|
| **CRITICAL** | >= 90% | Major factor rotation in progress |
| **ELEVATED** | 75-89% | Above-normal stress |
| Normal | < 75% | Baseline conditions |

---

## What Is This?

Lambda-F measures the **curvature** of the market's path through factor space—not just volatility (speed) or returns (direction).

When institutional investors rotate between factors simultaneously, the factor covariance matrix "twists." This non-commutativity is detectable before the price impact fully materializes.

---

## Validation Summary (15 Events, 6 Markets)

**Two-Signal System:** Lambda-F (rotation) + Correlation (synchronization)

| Market | Lambda-F Only | With Correlation | Key Events |
|--------|---------------|------------------|------------|
| **Commodities** | **3/3 (100%)** | **3/3 (100%)** | Q4 2018, WTI Negative, Ukraine |
| **Gold** | **2/2 (100%)** | **2/2 (100%)** | Q4 2018, $2000 Breakout |
| **Crypto** | **3/3 (100%)** | **3/3 (100%)** | April 2021, Nov 2021, March 2024 |
| **US Equity** | 2/3 (67%) | **3/3 (100%)** | 2007 GFC, 2022 Bear, **Q4 2018 (C)** |
| **UK Equity** | 1/2 (50%) | **2/2 (100%)** | Q4 2018, **Mini-budget (C)** |
| **Germany** | 1/2 (50%) | **2/2 (100%)** | Q4 2018, **Energy Crisis (C)** |
| **TOTAL** | **80% (12/15)** | **100% (15/15)** | + 4 black swans correctly excluded |

**Reading this table:**
- *Lambda-F Only* = Detection using rotation signal alone
- *With Correlation* = Detection using combined two-signal system
- **(C)** = Event detected by Correlation signal (synchronized selloff)
- Black swans (COVID, Terra, 3AC, FTX) correctly showed LOW on both signals

**Signal interpretation:**
- **(L)** = Lambda-F triggered (factor rotation detected)
- **(C)** = Correlation triggered (synchronized selloff detected)
- **(LC)** = Both signals triggered (maximum alert)

**Notable:** The October 2007 S&P 500 peak (pre-GFC) was detected with **86.5% peak percentile** and **57-day lead time**. The signal peaked during the BNP Paribas freeze (Aug 9, 2007) - the first public sign of subprime contagion.
---

## Real-Time Feed (Beta)

I'm building a real-time API with alerts. Interested in early access?

**[Join the Beta Waitlist](https://docs.google.com/forms/d/e/1FAIpQLSdo9MykqIj8n3_mJj54OzZNZ4P45Dg7GVBt0i4BqSHE1daSPQ/viewform)**

---

## Contact

R.J. Mathews | mail.rjmathews@gmail.com

Research use permitted with attribution
