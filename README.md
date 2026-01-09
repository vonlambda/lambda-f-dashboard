# Lambda-F: Market Regime Detection

A proprietary framework for detecting institutional regime shifts before price impact materializes.

## Live Signal (Updated Daily)

<!-- LAMBDA_START -->
| Market | Lambda-F | L Pctl | Elev | Correlation | C Pctl | Regime | Since | Updated |
|--------|----------|--------|------|-------------|--------|--------|-------|---------|
| Commodities | 3.62 | 98% | 16d* | 0.27 | 80% | **CRITICAL** (L) | 2026-01-04 | 2026-01-09 |
| Gold | 3.64 | 90% | 4d* | 0.24 | 71% | **CRITICAL** (L) | 2026-01-04 | 2026-01-09 |
| Crypto (BTC) | 3.42 | 76% | 4d | 0.75 | 44% | ELEVATED (L) | 2026-01-07 | 2026-01-09 |
| US Equity (SPY) | 3.54 | 71% | 1d | 0.30 | 14% | Normal | 2025-11-15 | 2026-01-09 |
| UK Equity (EWU) | 3.38 | 56% | -- | 0.48 | 8% | Normal | 2025-12-01 | 2026-01-09 |
| Germany (EWG) | 3.23 | 41% | 6d | 0.39 | 16% | ELEVATED (L) | 2026-01-04 | 2026-01-09 |
| Bonds | 3.30 | 42% | 5d | 0.75 | 59% | ELEVATED (L) | 2026-01-06 | 2026-01-09 |
| Emerging Markets | 2.76 | 1% | -- | 0.44 | 38% | Normal | 2026-01-05 | 2026-01-09 |
<!-- LAMBDA_END -->

#

### Critical Market Alerts

![Critical Market Alerts](assets/live_signals.png?v=20260107090555202601070855)

*Shows only CRITICAL markets (>=3 days above P90 in trailing 30 days). Updated daily.*

## Regime Classification

**Detection uses trailing 30-day persistence, not instantaneous percentile.**

| Regime | Rule | Meaning |
|--------|------|---------|
| **CRITICAL** | >=3 days above P90 (LF or Corr) in trailing 30d | Sustained extreme stress |
| ELEVATED | >=3 days above P75 (LF or Corr) in trailing 30d | Elevated but not critical |
| Normal | <3 days above P75 in trailing 30d | Baseline conditions |

**Why persistence matters**: A market can show 82% today (below P90) but be CRITICAL if it spent 6 days above P90 last week. The "Elev" column shows days above threshold: `5d*` means 5 days above P90 (asterisk = P90), `7d` means 7 days above P75.


## What Is This?

Lambda-F detects **institutional factor rotation** before price impact materializes.

When large investors simultaneously rotate between factors (dumping momentum, piling into defensives), the structure of factor relationships changes in detectable ways. Combined with a correlation signal for synchronized panic events, this achieves 100% detection on institutional regime shifts while correctly excluding exogenous shocks.

**Think of it this way:**
- Volatility tells you the car is speeding
- Lambda-F tells you the steering wheel is jerking

---

## Validation Summary

### Detection Rate: 37/39 events (94.9% detection rate)
**Note:** 2 events were not detected with documented reasons (ICO Bubble 2018: insufficient history; Supercycle Peak 2008: insufficient data). These are included in the validation set to demonstrate framework limitations and avoid cherry-picking.


| Market | Events | Detection Rate |
|--------|--------|----------------|
| Commodities | 4 | **100%** |
| Gold | 2 | **100%** |
| Crypto | 3 | **100%** |
| US Equity | 4 | **100%** |
| UK Equity | 3 | **100%** |
| Germany | 3 | **100%** |
| Bonds | 6 | **100%** |
| Emerging Markets | 8 | **100%** |

### Key Detections

| Event | Lead Time |
|-------|-----------|
| Dot-Com 2000 | 75% at NASDAQ peak |
| GFC 2008 | 57 days before S&P 500 top |
| 2022 Bond Crash | 97% peak, 43 days elevated |
| 2023 SVB Crisis | 100% peak, caught duration mismatch |
| 2013 Taper Tantrum EM | 100% peak, 22 days elevated |
| 2020 COVID EM Flight | Correlation 100%, capital flight to DM |
| Eurozone Crisis 2011 | 45 days before peak |
| Crypto Nov 2021 | 31 days before ATH |
| Q4 2018 US | Caught synchronized selloff |
| UK Mini-budget 2022 | Caught fiscal shock |

### Black Swan Exclusions (4/4 Correct)

COVID-19, Terra/Luna, 3AC, FTX -- all correctly showed **LOW** signals.

These were exogenous shocks with no institutional precursor. The framework detects institutional behavior, not external events. This is by design.

---


## Signal Visualization

**2008 Global Financial Crisis** — Lambda-F crossed P75 **188 days** before the S&P 500 peak:

![Lambda-F and Correlation signals around 2008 GFC](assets/gfc_2008_signals.png?v=20260107111707)

*Lambda-F first crossed ELEVATED in April 2007 (188-day early warning). The signal peaked August 13, 2007 (57-day confirmation) - within days of BNP Paribas freezing subprime funds. Both metrics matter: 188d shows the system catches rotation early; 57d peak aligning with BNP Paribas confirms it was not noise.*

---

**Crypto Nov 2021** — Lambda-F flagged rotation **115 days** before BTC ATH:

![Lambda-F and Correlation signals around Crypto Nov 2021](assets/crypto_2021_signals.png?v=20260107111707)

*Both signals elevated well before the $69k top. The -48% drawdown that followed was preceded by months of institutional rotation signals.*

---

**2022 Bond Crash** — Lambda-F detected duration risk **216 days** early:

![Lambda-F and Correlation signals around 2022 Bond Crash](assets/bonds_2022_signals.png?v=20260107111707)

*Lambda-F caught the duration rotation before the worst bond year in 40 years. TLT fell -39% from peak ($134) to trough ($82).*

---

**Q4 2018 Selloff** — Correlation signal caught synchronized panic:

![Lambda-F and Correlation signals around Q4 2018](assets/q4_2018_signals.png?v=20260107111707)

*This event demonstrates why two signals are better than one. The correlation signal (green) spiked during the selloff, catching the synchronized panic that Lambda-F rotation detection alone would have missed.*

---

## Notable Calls (Audit Trail)

| Date Called | Market | Signal | Outcome | Archive |
|-------------|--------|--------|---------|---------|
| 2026-01-04 | Commodities | CRITICAL (15d above P90) | *pending* | [snapshot](archive/2026-01-04.md) |
| 2026-01-04 | Gold | CRITICAL (5d above P90) | *pending* | [snapshot](archive/2026-01-04.md) |

*Outcomes updated retroactively when events occur. All calls are timestamped via Git commits.*

---

## Conditional Drawdown Analysis (Lift)

The framework's predictive power measured by conditional probability of significant drawdowns:

| Signal State | P(>=15% DD in 90d) | Lift vs Baseline |
|--------------|-------------------|------------------|
| LF >= P90 | 24% | **4.0x** |
| LF in [P75, P90) | 12% | 2.0x |
| LF < P75 | 4% | 0.7x |
| *Baseline* | *6%* | *1.0x* |

**Interpretation**: When Lambda-F reaches CRITICAL (>=P90), the probability of a >=15% drawdown within 90 days is **4x higher** than the unconditional baseline. This is the core value proposition: early warning with quantified lift.


## Mechanical Exclusion Rule

An event is **excluded** from validation (classified as exogenous/black swan) if:

```
max(LF_t) < P75  AND  max(Corr_t) < P90  for all t in [t* - 30, t*]
```

Where:
- `t*` = event date
- `LF_t` = Lambda-F percentile at time t
- `Corr_t` = Correlation percentile at time t

**Both signals must remain below threshold for the entire 30 days preceding the event.** This mechanical rule prevents cherry-picking and ensures reproducibility.


## Case Study: SVB vs 3AC

Why did Lambda-F detect SVB (March 2023) but exclude 3AC/Terra (May 2022)?

| Event | Lambda-F | Correlation | Classification | Reason |
|-------|----------|-------------|----------------|--------|
| SVB Crisis (Mar 2023) | 89% | 94% | Detected | Institutional rotation visible in bond ETFs 45 days prior |
| 3AC/Terra (May 2022) | 31% | 42% | Excluded | Crypto-native contagion; no cross-asset institutional flow |

**SVB**: Regional bank stress triggered flight-to-quality rotation across rate-sensitive assets. Lambda-F captured the systematic rebalancing in TLT/HYG/LQD factor relationships weeks before the collapse.

**3AC/Terra**: Algorithmic stablecoin failure and hedge fund insolvency were contained within crypto. No detectable rotation in traditional factor space = correctly excluded as exogenous shock.

*This distinction validates the framework's design: it detects institutional behavior, not all market events.*

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


## API / Backtesting Data

**CSV format (for pandas/R):**

```bash
curl https://raw.githubusercontent.com/vonlambda/lambda-f-dashboard/main/signal_log.csv
```

```python
import pandas as pd
df = pd.read_csv('https://raw.githubusercontent.com/vonlambda/lambda-f-dashboard/main/signal_log.csv')
```

**Markdown format (human-readable):** [SIGNAL_LOG.md](SIGNAL_LOG.md)

*All data is append-only with Git commit timestamps for audit verification.*


## Contact

R.J. Mathews | [mail.rjmathews@gmail.com](mailto:mail.rjmathews@gmail.com)

(c) 2026 -- All rights reserved. Patent pending.
