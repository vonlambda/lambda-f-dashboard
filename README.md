# Lambda-F: Factor Rotation Stress Monitor

A Lie algebra-based framework for detecting market regime shifts through non-commutativity of factor covariance dynamics.

## Live Signal (Updated Daily)

<!-- LAMBDA_START -->
| Market | Lambda-F | Percentile | Regime | Since | Last Updated |
|--------|----------|------------|--------|-------|--------------|
| Commodities | 3.57 | 96% | **CRITICAL** | Dec 18 | 2026-01-04 |
| Gold | 3.57 | 80% | ELEVATED | Dec 22 | 2026-01-04 |
| Crypto (BTC) | 3.19 | 40% | Normal | Jan 02 | 2026-01-04 |
| US Equity (SPY) | 3.49 | 65% | Normal | Nov 15 | 2026-01-04 |
| UK Equity (EWU) | 3.29 | 45% | Normal | Dec 01 | 2026-01-04 |
| Germany (EWG) | 3.14 | 23% | Normal | Dec 01 | 2026-01-04 |
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

## Validation Summary

| Market | Backtest Accuracy | Events Flagged (Missed) |
|--------|-------------------|-------------------------|
| Commodities | 100% (3/3) | Q4 2018, WTI Negative, Ukraine |
| Gold | 100% (2/2) | Q4 2018, $2000 Breakout |
| Crypto | 67% (2/3) | Nov 2021, FTX (missed: Terra) |

*Backtest Accuracy = % of major events where Lambda-F crossed P75 threshold before the event.*

---

## Real-Time Feed (Beta)

I'm building a real-time API with alerts. Interested in early access?

**[â†’ Join the Beta Waitlist](https://docs.google.com/forms/d/e/1FAIpQLSdo9MykqIj8n3_mJj54OzZNZ4P45Dg7GVBt0i4BqSHE1daSPQ/viewform)**

---

## Contact

R.J. Mathews | mail.rjmathews@gmail.com

Research use permitted with attribution
