# Lambda-F: Two-Signal Market Regime Detector

A framework for detecting market regime shifts through **non-commutativity of factor covariance dynamics**, enhanced with correlation synchronization detection.

## Live Signal (Updated Daily)

<!-- LAMBDA_START -->
| Market | Lambda-F | L Pctl | Correlation | C Pctl | Regime | Since | Updated |
|--------|----------|--------|-------------|--------|--------|-------|---------|
| Commodities | 3.57 | 96% | 0.25 | 76% | **CRITICAL** (L) | 2025-01-04 | 2026-01-04 |
| Gold | 3.57 | 80% | 0.22 | 55% | **CRITICAL** (L) | 2025-01-04 | 2026-01-04 |
| Crypto (BTC) | 3.19 | 40% | 0.82 | 67% | Normal | 2026-01-02 | 2026-01-04 |
| US Equity (SPY) | 3.49 | 65% | 0.33 | 26% | Normal | 2025-11-15 | 2026-01-04 |
| UK Equity (EWU) | 3.29 | 45% | 0.51 | 12% | Normal | 2025-12-01 | 2026-01-04 |
| Germany (EWG) | 3.14 | 23% | 0.46 | 22% | Normal | 2025-12-01 | 2026-01-04 |
<!-- LAMBDA_END -->

### Signal Interpretation

| Signal | Threshold | What It Detects |
|--------|-----------|-----------------|
| **Lambda-F (L)** | >= P75 | Factor rotation (institutional repositioning) |
| **Correlation (C)** | >= P90 | Synchronized selloff (assets moving together) |

| Regime | Condition | Action |
|--------|-----------|--------|
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

See [`events.csv`](events.csv) for the full audit trail with dates and detection details.

### Signal Distribution

| Signal Type | Events | Example |
|-------------|--------|---------|
| Lambda-F only | 13 | Oil Bust 2014-16 (96.7%, 115 days elevated) |
| Correlation only | 2 | Q4 2018 US (96.7% correlation spike) |
| Both signals | 3 | 2011 Eurozone Crisis (L: 99%, C: 100%) |

### Black Swans Correctly Excluded

COVID, Terra, 3AC, FTX -- all showed LOW on both signals. No institutional precursor = no signal. This is expected behavior for a factor rotation detector.

---

## What Is This?

**Lambda-F** measures the **non-commutativity** of the factor covariance matrix evolution:

```
Lambda_F = ||[F, dF/dt]||_F / (||F||_F * ||dF/dt||_F)
```

When institutions rotate between factors simultaneously, the covariance matrix eigenvectors rotate rapidly. This "rotational strength" is detectable before price impact fully materializes.

**Correlation** measures synchronization -- when all assets move together. Catches sudden panic selloffs and policy shocks.

**Combined:** Either signal elevated = regime flagged. Achieves 100% detection on institutional events while correctly excluding exogenous shocks.

---

## Methodology

### Percentile Calculation

- **Reference:** Trailing 252-day rolling window
- **Computed on:** Smoothed Lambda-F (EMA + 14-day smoothing)
- **Updated:** Daily

### Parameters (Validated)

| Parameter | Value | Description |
|-----------|-------|-------------|
| Window | 105 days | Covariance estimation (~5 months) |
| EMA Span | 5 days | Factor smoothing |
| Smoothing | 14 days | Output smoothing |
| Correlation Window | 21 days | Pairwise correlation (~1 month) |
| Lookback | 252 days | Percentile reference (~1 year) |

See [`METHODOLOGY.md`](METHODOLOGY.md) for full technical details.

---

## Run Locally

```bash
# Clone
git clone https://github.com/vonlambda/lambda-f-dashboard.git
cd lambda-f-dashboard

# Install
pip install -r requirements.txt

# Configure (optional - for GitHub push)
cp .env.example .env
# Edit .env with your GitHub token

# Run
python update_lambda.py
```

**Requirements:** Python 3.10+, no API keys needed (uses Yahoo Finance).

---

## Data Sources

All data from Yahoo Finance. Availability may vary:

| Market | Tickers | History |
|--------|---------|---------|
| Commodities | GLD, SLV, USO, UNG, CPER, DBA | 2007+ |
| Gold | GLD, SLV, GDX, GDXJ, UUP, TLT | 2007+ |
| Crypto | BTC-USD, ETH-USD, LTC-USD, XRP-USD | 2017+ |
| US Equity | XLF, XLK, XLE, XLV, XLI, XLP, XLY, XLB | 2000+ |
| UK/Germany | EWU, EWG, etc. | 2005+ |

---

## Real-Time Feed (Beta)

Building a real-time API with alerts. Interested in early access?

**[Join the Beta Waitlist](https://docs.google.com/forms/d/e/1FAIpQLSdo9MykqIj8n3_mJj54OzZNZ4P45Dg7GVBt0i4BqSHE1daSPQ/viewform)**

---

## License

MIT License. See [LICENSE](LICENSE).

**Disclaimer:** This is research software, not financial advice. Past detection does not guarantee future performance.

---

## Contact

R.J. Mathews | mail.rjmathews@gmail.com

Research use permitted with attribution.
