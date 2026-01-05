# Pre-Registration Protocol

## Validation Methodology

This document defines the exact protocol used to evaluate Lambda-F detection performance. Parameters and event list were fixed **before** running the final validation.

---

## Event Selection Criteria

Events were selected based on:

1. **Widely-recognized market stress episodes** documented in financial media
2. **Clear peak/trough dates** identifiable in price data
3. **Minimum 20% drawdown** from peak to trough (for equity/crypto)
4. **Available data** for the relevant market/tickers

**Selection was NOT based on:**
- Lambda-F signal strength during the event
- Whether the framework "would have detected" the event
- Post-hoc fitting to results

---

## Parameter Specification (Fixed)

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| WINDOW | 105 | ~5 months covariance estimation |
| EMA_SPAN | 5 | Smoothing factor returns |
| SMOOTH_DAYS | 14 | Output smoothing |
| LAMBDA_LAG | 2 | Avoid same-day look-ahead |
| CORR_WINDOW | 21 | ~1 month correlation |
| LOOKBACK_DAYS | 252 | ~1 year percentile reference |
| P75_THRESHOLD | 0.75 | Elevated signal |
| P90_THRESHOLD | 0.90 | Critical signal |
| PERSISTENCE | 3 days | Minimum days above threshold |

These parameters were optimized on 2019-2021 crypto data and validated out-of-sample on 2021-2025 data. They were NOT tuned on the full event set.

---

## Detection Criteria

An event is "detected" if:

1. **Lambda-F signal:** ≥3 days above P75 in the 60-day window before/during the event peak
2. **Correlation signal:** ≥3 days above P90 in the 60-day window before/during the event peak
3. **Combined:** Either signal triggers = event detected

---

## False Positive Analysis

**Definition:** Days in ELEVATED or CRITICAL regime when no event is occurring.

**Expected baseline (by construction):**
- P75 threshold → ~25% of days expected above threshold
- P90 threshold → ~10% of days expected above threshold
- With 3-day persistence requirement → lower effective rate

**Observed rates (to be computed per market):**

| Market | Total Days | Days Elevated (L) | Days Critical (L) | Days Elevated (C) | Days Critical (C) |
|--------|------------|-------------------|-------------------|-------------------|-------------------|
| Crypto | TBD | TBD | TBD | TBD | TBD |
| US Equity | TBD | TBD | TBD | TBD | TBD |
| Commodities | TBD | TBD | TBD | TBD | TBD |

---

## Baseline Comparisons

To contextualize Lambda-F performance, we compare against:

1. **Correlation-only:** Average pairwise correlation > P90
2. **Volatility-only:** Realized volatility (21-day) > P90
3. **Drawdown filter:** Price > 10% below 60-day high
4. **Random baseline:** 25% of days flagged randomly

| Baseline | Events Detected (18) | False Positive Rate |
|----------|---------------------|---------------------|
| Lambda-F only | 16/18 | TBD |
| Correlation only | 5/18 | TBD |
| Volatility only | TBD | TBD |
| Drawdown filter | TBD | TBD |
| Lambda-F + Corr | 18/18 | TBD |

---

## Event List (Fixed)

See [`events.csv`](events.csv) for the complete list with:
- Event ID
- Event name
- Market
- Start/end dates
- Event type
- Detection result
- Signal source

---

## Reproducibility

To reproduce this validation:

```bash
git clone https://github.com/vonlambda/lambda-f-dashboard.git
cd lambda-f-dashboard
pip install -r requirements.txt
python validate_events.py
```

The script will:
1. Fetch historical data from Yahoo Finance
2. Compute Lambda-F and Correlation for each market
3. Evaluate detection against the fixed event list
4. Output results matching `events.csv`

---

## Known Limitations

1. **Pre-2007 data:** Limited ETF availability
2. **Crypto pre-2017:** Insufficient market diversity
3. **Black swans:** By design, exogenous shocks are not detected
4. **Slow drift:** Multi-year trends may not trigger either signal
5. **Data quality:** Yahoo Finance data may have gaps

---

## Changelog

- **2026-01-05:** Initial protocol with 18 events + 4 black swans
- Parameters fixed based on walk-forward validation

