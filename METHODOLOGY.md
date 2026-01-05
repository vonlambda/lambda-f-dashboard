# Lambda-F Methodology

## Signal Definitions

### Lambda-F (Factor Rotation)

**What it measures:** Non-commutativity of the factor covariance matrix evolution, detecting when institutional investors rotate between factors simultaneously.

**Formula:**
```
Lambda_F = ||[F, dF/dt]||_F / (||F||_F * ||dF/dt||_F)
```

Where:
- `F` = factor covariance matrix (4x4)
- `[A, B] = AB - BA` = matrix commutator
- `||.||_F` = Frobenius norm

**Interpretation:** When Lambda-F is high, the eigenvectors of the covariance matrix are rotating rapidly -- institutions are repositioning across factor exposures.

### Correlation (Synchronized Selloff)

**What it measures:** Average pairwise correlation across all assets, detecting when everything moves together (panic selling).

**Formula:**
```
Correlation = mean(upper_triangle(rolling_corr_matrix))
```

**Interpretation:** When correlation is high, diversification breaks down -- assets that normally move independently are moving in lockstep.

---

## Parameters (Fixed/Validated)

| Parameter | Value | Description |
|-----------|-------|-------------|
| `WINDOW` | 105 | Rolling window for covariance estimation (~5 months) |
| `EMA_SPAN` | 5 | Exponential smoothing span for factor returns |
| `SMOOTH_DAYS` | 14 | Final smoothing on Lambda-F output |
| `LAMBDA_LAG` | 2 | Lag applied to Lambda-F (avoids look-ahead) |
| `CORR_WINDOW` | 21 | Rolling window for correlation (~1 month) |
| `LOOKBACK_DAYS` | 252 | Percentile reference window (~1 year) |
| `PERSISTENCE` | 3 days | Minimum days above threshold to flag |

**These parameters were optimized on 2019-2021 crypto data and fixed before final validation.**

---

## Percentile Calculation

**Reference Distribution:** Trailing 252-day rolling window of daily values.

**Computed On:** Smoothed Lambda-F series (after EMA and 14-day smoothing).

**Update Frequency:** Daily (percentile thresholds recalculated each day based on trailing window).

**Critical:** Percentiles use ONLY past data available at each time t. No look-ahead.

**Thresholds:**
- P75 = 75th percentile of trailing 252 days (ELEVATED trigger for Lambda-F)
- P90 = 90th percentile of trailing 252 days (CRITICAL trigger for Lambda-F)
- P90/P95 = Triggers for Correlation signal

---

## False Positive Rates

**Expected baseline (by construction):**

| Threshold | Expected Rate | Observed Rate |
|-----------|---------------|---------------|
| Lambda > P75 | 25% (~63 days/yr) | 25% |
| Lambda > P90 | 10% (~25 days/yr) | 10% |
| Corr > P90 | 10% (~25 days/yr) | 10% |
| Corr > P95 | 5% (~13 days/yr) | 5% |

The observed rates match expectations, indicating well-calibrated percentile thresholds.

**With 3-day persistence requirement:** Effective false positive rate is lower, as transient spikes are filtered out.

---

## Regime Classification

**Detection Logic (Trailing 30-Day Window):**

| Regime | Condition |
|--------|-----------|
| **CRITICAL** | >=3 days above P90 (Lambda-F) OR >=3 days above P95 (Correlation) |
| **ELEVATED** | >=3 days above P75 (Lambda-F) OR >=3 days above P90 (Correlation) |
| **Normal** | Below thresholds |

**Signal Source Indicators:**
- `(L)` = Lambda-F triggered
- `(C)` = Correlation triggered
- `(LC)` = Both signals triggered

---

## Factor Construction

For each market, we construct 4 factors from constituent returns:

| Factor | Construction |
|--------|--------------|
| **CMKT** | Equal-weighted mean of all constituent returns |
| **CSMB** | Long top 50% by 30-day performance, short bottom 50% |
| **CMOM** | Long top 50% by 14-day momentum, short bottom 50% |
| **CVOL** | Mean of 14-day rolling volatility across constituents |

**Note:** This uses performance-based ranking, not market-cap weighting. All scripts use the same canonical definition from `lambda_factors.py`.

---

## Data Sources

| Market | Tickers | Source |
|--------|---------|--------|
| Commodities | GLD, SLV, USO, UNG, CPER, DBA | Yahoo Finance |
| Gold | GLD, SLV, GDX, GDXJ, UUP, TLT | Yahoo Finance |
| Crypto | BTC-USD, ETH-USD, LTC-USD, XRP-USD | Yahoo Finance |
| US Equity | XLF, XLK, XLE, XLV, XLI, XLP, XLY, XLB | Yahoo Finance |
| UK Equity | EWU, FXB, EWUS, EWL | Yahoo Finance |
| Germany | EWG, EWL, EWN, EWO, FXE | Yahoo Finance |

**Note:** Data availability may vary. Some ETFs have limited history (post-2007).

---

## Validation Methodology

See [PROTOCOL.md](PROTOCOL.md) for the full pre-registration protocol.

**Event Labeling:** Events are labeled retrospectively based on widely-recognized market stress episodes. See `events.csv` for the full list with dates.

**Detection Criteria:** An event is "detected" if either signal exceeds its threshold for >=3 days in the 60-day window before/during the event peak.

**Black Swan Exclusion:** Events with no institutional precursor (COVID, Terra, 3AC, FTX) correctly show LOW on both signals. This is expected behavior -- the framework detects factor rotation, not exogenous shocks.

---

## Limitations

1. **Pre-2007 data:** Many ETFs did not exist, limiting historical validation.
2. **Slow drift events:** Multi-year trends may not spike either signal.
3. **Black swans:** By design, exogenous shocks without institutional precursors are not detected.
4. **Data quality:** Yahoo Finance data may have gaps or adjustments.
5. **Percentile calibration:** Initial warmup period (252 days) required for stable percentiles.

---

## Reproducibility

To reproduce the validation:

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run validation: `python validate_events.py`
4. Compare output against `events.csv`

All parameters are pinned in the code. No manual adjustments are made post-hoc.
