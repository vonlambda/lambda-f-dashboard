# Lambda-F: Two-Signal Market Regime Detection

A framework for detecting market regime shifts through factor covariance dynamics, combining rotation detection (Lambda-F) with correlation synchronization.

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

| Regime | Condition | Interpretation |
|--------|-----------|----------------|
| **CRITICAL** | Lambda >= P90 OR Corr >= P95 | Major regime shift in progress |
| **ELEVATED** | Lambda >= P75 OR Corr >= P90 | Above-normal stress |
| Normal | Below thresholds | Baseline conditions |

### Signal Attribution

| Code | Meaning |
|------|---------|
| L | Lambda-F triggered (factor rotation) |
| C | Correlation triggered (synchronized panic) |
| LC | Both signals triggered (maximum stress) |

---

## What Is This?

Lambda-F is a **two-signal detection system** for market regime shifts:

1. **Lambda-F (Rotation):** Measures non-commutativity of factor covariance evolution. When institutional investors rotate between factors (e.g., dumping momentum, buying defensives), the factor covariance matrix "twists." This is detectable before price impact materializes.

2. **Correlation (Synchronization):** Measures average pairwise correlation among factors. When all factors move together (panic selloffs), correlation spikes even without rotation.

**Think of it this way:**
- Volatility tells you how fast the car is going
- Lambda-F tells you the steering wheel is jerking (rotation)
- Correlation tells you all cars on the highway are swerving the same direction (synchronized panic)

---

## Validation Summary

### Two-Signal Detection: 18/18 Events (100%)

| Market | Events | Lambda-F | Correlation | Combined |
|--------|--------|----------|-------------|----------|
| Commodities | 4 | 4/4 | -- | **100%** |
| Gold | 2 | 2/2 | -- | **100%** |
| Crypto | 3 | 3/3 | -- | **100%** |
| US Equity | 3 | 2/3 | 1/3 | **100%** |
| UK Equity | 3 | 2/3 | 1/3 | **100%** |
| Germany | 3 | 2/3 | 1/3 | **100%** |
| **TOTAL** | **18** | 15 | 3 | **100%** |

### Key Detections

| Event | Year | Peak Signal | Lead Time | Signal Type |
|-------|------|-------------|-----------|-------------|
| GFC | 2007-08 | 86.5% | 57 days | L |
| Eurozone Crisis | 2011 | 99.9% / 100% | 45 days | LC |
| 2014-16 Oil Bust | 2014-16 | 96.7% | 115 days | L |
| Q4 2018 US | 2018 | 96.7% (Corr) | 33 days | C |
| UK Mini-budget | 2022 | 98.7% (Corr) | 33 days | C |
| Crypto Nov 2021 | 2021 | 92% | 31 days | L |

### Black Swan Exclusions (4/4 Correct)

| Event | Lambda-F | Correlation | Reason |
|-------|----------|-------------|--------|
| COVID-19 (Mar 2020) | LOW | -- | Exogenous pandemic |
| Terra/Luna (May 2022) | LOW | LOW | Algorithmic failure |
| 3AC/Celsius (Jun 2022) | LOW | LOW | Counterparty contagion |
| FTX (Nov 2022) | LOW | LOW | Fraud |

---

## Methodology

### Factor Construction

**Constructed Factors** (Crypto):
- **CMKT:** Equal-weighted market return
- **CSPREAD:** Cross-sectional spread (top vs bottom 30-day performers)
- **CMOM:** 14-day momentum long-short
- **CVOL:** Normalized dollar volume

**Proxy Factors** (Equities, Commodities):
- Sector ETF returns as basis vectors

### Lambda-F Computation

```
1. EMA smoothing (span=5) on factor returns
2. Rolling standardization (window=105 days)
3. Compute rolling covariance matrix F(t)
4. Numerical derivative: dF/dt = F(t) - F(t-1)
5. Commutator: [F, dF] = F*dF - dF*F
6. Lambda_F = log(1 + 100 * ||[F,dF]||_F / (||F||_F * ||dF||_F))
7. 14-day smoothing + 2-day lag
```

### Correlation Signal

```
rho_t = (2 / k(k-1)) * sum_{i<j} corr_21(f_i, f_j)
```

Average pairwise correlation over 21-day trailing window.

### Ex-Ante Percentile Computation

**Critical:** All percentiles use only trailing data (no look-ahead):

```python
percentile = signal.expanding(min_periods=252).rank(pct=True) * 100
```

This ensures all published results are achievable in real-time deployment.

---

## Signal Complementarity

| Event Type | Primary Signal | Example |
|------------|----------------|---------|
| Gradual institutional rotation | Lambda-F | GFC 2008, 2022 Bear, Oil Bust |
| Synchronized panic/selloff | Correlation | Q4 2018 US, UK Mini-budget |
| Maximum stress (both) | Lambda-F + Correlation | 2011 Eurozone Crisis |

**Why two signals?**
- Lambda-F alone: 83% detection (misses synchronized selloffs)
- Correlation alone: 28% detection (misses gradual rotations)
- Combined: 100% detection

---

## Limitations

1. **Black swan blindness:** Does not detect exogenous shocks (COVID, hacks, fraud). This is by design - the framework detects institutional behavior, not external events.

2. **Pre-institutional markets:** 2017 crypto top was missed because CME futures launched Dec 17, 2017 (the top day). Institutional infrastructure didn't exist.

3. **Parameter sensitivity:** Optimized for post-2018 institutional markets. Pre-2018 detection less reliable.

---

## Real-Time Feed (Beta)

Building a real-time API with alerts. Interested in early access?

**[Join the Beta Waitlist](https://docs.google.com/forms/d/e/1FAIpQLSdo9MykqIj8n3_mJj54OzZNZ4P45Dg7GVBt0i4BqSHE1daSPQ/viewform)**

---

## Research

Full methodology in [Lambda-F Paper (PDF)](docs/lambda_hmm_paper_v2.pdf)

Patent pending: US Provisional Application (Two-Signal Detection System)

---

## Contact

R.J. Mathews | mail.rjmathews@gmail.com

(c) 2026 - Research use permitted with attribution. Commercial use requires license.
