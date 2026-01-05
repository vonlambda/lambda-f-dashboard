# Lambda-F: Factor Rotation Stress Monitor

A Lie algebra-based framework for detecting market regime shifts through non-commutativity of factor covariance dynamics.

## Live Signal (Updated Daily)

<!-- LAMBDA_START -->
| Market | Lambda-F | Percentile | Regime | Since | Last Updated |
|--------|----------|------------|--------|-------|--------------|
| Commodities | 3.57 | 96% | **CRITICAL** | Dec 18 | 2026-01-04 |
| Gold | 3.57 | 80% | **CRITICAL** | Jan 04 | 2026-01-04 |
| Crypto (BTC) | 3.19 | 40% | Normal | Jan 02 | 2026-01-04 |
| US Equity (SPY) | 3.49 | 65% | Normal | Nov 15 | 2026-01-04 |
| UK Equity (EWU) | 3.29 | 45% | Normal | Dec 01 | 2026-01-04 |
| Germany (EWG) | 3.14 | 23% | ELEVATED | Jan 04 | 2026-01-04 |
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

## Validation Summary (18 Events, 6 Markets)

| Market | Rotations Flagged | Black Swans Excluded | Key Events |
|--------|-------------------|---------------------|------------|
| **Commodities** | **3/3 (100%)** | - | Q4 2018, WTI Negative, Ukraine |
| **Gold** | **2/2 (100%)** | - | Q4 2018, $2000 Breakout |
| **Crypto** | **3/3 (100%)** | 3/3 correct | April 2021, Nov 2021, March 2024 |
| **US Equity** | **2/3 (67%)** | 1/1 correct | **2007 GFC**, 2022 Bear, Q4 2018 missed |
| UK Equity | 1/2 (50%) | - | Q4 2018, Mini-budget missed |
| Germany | 1/2 (50%) | - | Q4 2018, Energy Crisis missed |

**Reading this table:**
- *Rotations Flagged* = Institutional repositioning events where Lambda-F crossed P75 before the event
- *Black Swans Excluded* = External shocks (COVID, Terra, FTX) that correctly showed LOW Lambda-F

The framework detects **factor rotation**, not all crashes. Black swans show LOW because there's no institutional repositioning to detect - this is correct behavior.

**Notable:** The October 2007 S&P 500 peak (pre-GFC) was detected with **86.5% peak percentile** and **57-day lead time**. The signal peaked during the BNP Paribas freeze (Aug 9, 2007) - the first public sign of subprime contagion.

**Notable:** The October 2007 S&P 500 peak (pre-GFC) was detected with **86.5% peak percentile** and **57-day lead time**. The signal peaked during the BNP Paribas freeze (Aug 9, 2007) - the first public sign of subprime contagion.

---

## Real-Time Feed (Beta)

I'm building a real-time API with alerts. Interested in early access?

**[Join the Beta Waitlist](https://docs.google.com/forms/d/e/1FAIpQLSdo9MykqIj8n3_mJj54OzZNZ4P45Dg7GVBt0i4BqSHE1daSPQ/viewform)**

---

## Contact

R.J. Mathews | mail.rjmathews@gmail.com

Research use permitted with attribution
